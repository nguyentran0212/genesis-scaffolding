from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast

from myproject_core.schemas import WorkflowCallback
from myproject_core.workflow_engine import WorkflowEngine
from myproject_core.workflow_registry import WorkflowRegistry
from sqlmodel import Session

from ..database import engine as db_engine
from ..models.workflow_job import JobStatus, WorkflowJob


async def add_workflow_job(
    inputs: dict[str, Any], user_inbox: Path, user_id: int, workflow_id: str
) -> WorkflowJob | None:
    """
    Register a workflow job in the database
    Also resolve the relative path user provides in workflow input to the correct path under their sandbox
    """
    resolved_inputs = inputs.copy()
    if "input_files" in resolved_inputs:
        files = resolved_inputs["input_files"]
        if isinstance(files, list):
            resolved_inputs["input_files"] = [
                str(user_inbox / f) if not Path(f).is_absolute() else f for f in files
            ]
        elif isinstance(files, str):
            resolved_inputs["input_files"] = (
                str(user_inbox / files) if not Path(files).is_absolute() else files
            )

    with Session(db_engine) as session:
        # Create Job Record with RESOLVED inputs
        job = WorkflowJob(
            workflow_id=workflow_id,
            user_id=user_id,
            inputs=resolved_inputs,  # Use resolved paths here
            status=JobStatus.PENDING,
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        return job


async def run_workflow_job(
    job_id: int,
    engine_instance: WorkflowEngine,
    registry_instance: WorkflowRegistry,
    inputs: dict[str, Any] | None = None,
    workflow_callbacks: list[WorkflowCallback] | None = None,
) -> WorkflowJob | None:
    """
    Run a registered workflow job
    """
    with Session(db_engine) as session:
        job = session.get(WorkflowJob, job_id)
        if not job:
            return

        try:
            job.status = JobStatus.RUNNING
            session.add(job)
            session.commit()

            manifest = registry_instance.get_workflow(job.workflow_id)
            if not manifest:
                raise ValueError(f"Workflow type not found: {job.workflow_id}")

            # If user provides inputs, then use the input to run the workflow
            # Otherwise, try to use the input already registered in the database
            # If there is no workflow input to be found, throw exception
            workflow_inputs = job.inputs
            if inputs:
                workflow_inputs = inputs
            if not workflow_inputs:
                raise Exception(f"Could not find the inputs for workflow job {job_id}")

            workflow_output = await engine_instance.run(
                manifest,
                workflow_inputs,
                workflow_callbacks,
            )

            job.status = JobStatus.COMPLETED
            job.result = workflow_output.workflow_result
            job.workspace_path = str(workflow_output.workspace_directory)

        except Exception as e:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
        finally:
            job.updated_at = datetime.now(timezone.utc)
            session.add(job)
            session.commit()
            session.refresh(job)
        return job
