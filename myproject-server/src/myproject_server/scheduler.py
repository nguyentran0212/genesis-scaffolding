import logging
from datetime import datetime, timezone
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from myproject_core.workflow_engine import WorkflowEngine
from myproject_core.workflow_registry import WorkflowRegistry
from sqlmodel import Session, select

from .database import engine as db_engine
from .models.workflow_schedule import WorkflowSchedule
from .utils.workflow_job import add_workflow_job, run_workflow_job

logger = logging.getLogger(__name__)


class SchedulerManager:
    def __init__(self, engine: WorkflowEngine, registry: WorkflowRegistry):
        self.scheduler = AsyncIOScheduler()
        self.engine = engine
        self.registry = registry

    def start(self):
        if not self.scheduler.running:
            self.scheduler.start()

    async def sync_schedules(self):
        """Initial sync on server start."""
        with Session(db_engine) as session:
            statement = select(WorkflowSchedule).where(WorkflowSchedule.enabled)
            for schedule in session.exec(statement).all():
                self.upsert_schedule(schedule)

    def upsert_schedule(self, schedule: WorkflowSchedule):
        """Register or update the cron job in memory."""
        job_id = f"sched_{schedule.id}"
        trigger = CronTrigger.from_crontab(schedule.cron_expression, timezone=schedule.timezone)

        self.scheduler.add_job(
            self._execute_scheduled_task,
            trigger=trigger,
            id=job_id,
            args=[schedule.id],
            replace_existing=True,
        )

    def remove_schedule(self, schedule_id: int):
        self.scheduler.remove_job(f"sched_{schedule_id}")

    async def _execute_scheduled_task(self, schedule_id: int):
        with Session(db_engine) as session:
            schedule = session.get(WorkflowSchedule, schedule_id)
            if not schedule or not schedule.enabled:
                return

            # Use the directory captured in the DB
            user_inbox = Path(schedule.user_directory)

            # 1. Create the job record using existing util
            job = await add_workflow_job(
                inputs=schedule.inputs,
                user_inbox=user_inbox,
                user_id=schedule.user_id,
                workflow_id=schedule.workflow_id,
            )

            if job and job.id:
                # Link job to schedule and update timestamp
                job.schedule_id = schedule.id
                schedule.last_run_at = datetime.now(timezone.utc)
                session.add(job)
                session.add(schedule)
                session.commit()

                # 2. Run the job
                await run_workflow_job(
                    job_id=job.id, engine_instance=self.engine, registry_instance=self.registry
                )
