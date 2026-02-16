import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Any, cast

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
from myproject_core.schemas import WorkflowCallback, WorkflowEvent
from myproject_core.workflow_engine import WorkflowEngine
from myproject_core.workflow_registry import WorkflowRegistry
from sqlmodel import Session, desc, select
from sse_starlette.sse import EventSourceResponse

from ..database import engine as db_engine
from ..database import get_session
from ..dependencies import (
    get_current_active_user,
    get_user_inbox_path,
    get_workflow_engine,
    get_workflow_registry,
)
from ..models.user import User
from ..models.workflow_job import JobStatus, WorkflowJob
from ..schemas.workflow_job import WorkflowJobRead, WorkflowRunResponse

# Global store: {user_id: {job_id: asyncio.Queue}}
job_streams: dict[int, dict[int, asyncio.Queue]] = {}


def get_job_queue(user_id: int, job_id: int) -> asyncio.Queue | None:
    return job_streams.get(user_id, {}).get(job_id)


def create_job_queue(user_id: int, job_id: int) -> asyncio.Queue:
    if user_id not in job_streams:
        job_streams[user_id] = {}
    queue = asyncio.Queue()
    job_streams[user_id][job_id] = queue
    return queue


class ServerSSERenderer:
    """
    Implements the WorkflowCallback interface to push events to SSE.
    """

    def __init__(self, user_id: int, job_id: int):
        self.user_id = user_id
        self.job_id = job_id

    async def __call__(self, event: WorkflowEvent) -> None:
        """
        The actual callback matching WorkflowCallback type.
        """
        queue = get_job_queue(self.user_id, self.job_id)
        if queue:
            # We wrap the event in a dict for SSE-friendly JSON serialization
            await queue.put(
                {
                    "event": event.event_type.value,
                    "data": {"step_id": event.step_id, "message": event.message, "data": event.data},
                }
            )


async def run_workflow_background(
    user_id: int,
    job_id: int,
    workflow_id: str,
    inputs: dict[str, Any],
    engine_instance: WorkflowEngine,
    registry_instance: WorkflowRegistry,
):
    # This instance is a WorkflowCallback
    sse_callback = ServerSSERenderer(user_id, job_id)

    with Session(db_engine) as session:
        job = session.get(WorkflowJob, job_id)
        if not job:
            return

        try:
            job.status = JobStatus.RUNNING
            session.add(job)
            session.commit()

            manifest = registry_instance.get_workflow(workflow_id)
            if not manifest:
                raise ValueError(f"Workflow type not found: {workflow_id}")

            # Pass our callback in the list
            # engine.run(manifest, inputs, [sse_callback])
            workflow_output = await engine_instance.run(
                manifest, inputs, [cast(WorkflowCallback, sse_callback)]
            )

            job.status = JobStatus.COMPLETED
            job.result = workflow_output.workflow_result
            job.workspace_path = str(workflow_output.workspace_directory)

            # Emit a final status event manually or via a log event
            queue = get_job_queue(user_id, job_id)
            if queue:
                await queue.put({"event": "status", "data": "COMPLETED"})

        except Exception as e:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            queue = get_job_queue(user_id, job_id)
            if queue:
                await queue.put({"event": "error", "data": str(e)})
        finally:
            job.updated_at = datetime.now(timezone.utc)
            session.add(job)
            session.commit()


router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/", response_model=WorkflowRunResponse)
async def submit_job(
    workflow_id: str,
    inputs: dict[str, Any],
    background_tasks: BackgroundTasks,
    user: Annotated[User, Depends(get_current_active_user)],
    user_inbox: Annotated[Path, Depends(get_user_inbox_path)],
    session: Annotated[Session, Depends(get_session)],
    registry: Annotated[WorkflowRegistry, Depends(get_workflow_registry)],
    engine: Annotated[WorkflowEngine, Depends(get_workflow_engine)],
):
    # 1. Verify Workflow Exists before doing any work
    manifest = registry.get_workflow(workflow_id)
    if not manifest:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # 2. Path Resolution (The "CLI logic" adapted for User Sandbox)
    # We resolve 'input_files' relative to the user_inbox path provided by dependency
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

    # 3. Create Job Record with RESOLVED inputs
    job = WorkflowJob(
        workflow_id=workflow_id,
        user_id=cast(int, user.id),
        inputs=resolved_inputs,  # Use resolved paths here
        status=JobStatus.PENDING,
    )
    session.add(job)
    session.commit()
    session.refresh(job)

    # 4. Prepare Types for Background Task
    safe_job_id = cast(int, job.id)
    safe_user_id = cast(int, user.id)

    # 5. Initialize the user-scoped SSE queue
    create_job_queue(safe_user_id, safe_job_id)

    # 6. Dispatch Background Task with RESOLVED inputs
    background_tasks.add_task(
        run_workflow_background,
        safe_user_id,
        safe_job_id,
        workflow_id,
        resolved_inputs,  # Pass the resolved paths to the engine
        engine,
        registry,
    )

    return {"message": "Job submitted", "job_id": safe_job_id}


@router.get("/", response_model=list[WorkflowJobRead])
async def list_jobs(
    user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[Session, Depends(get_session)],
    offset: int = 0,
    limit: int = 20,
):
    """
    Get all jobs for the current user, ordered by newest first.
    """
    statement = (
        select(WorkflowJob)
        .where(WorkflowJob.user_id == user.id)
        .order_by(desc(WorkflowJob.created_at))
        .offset(offset)
        .limit(limit)
    )
    jobs = session.exec(statement).all()
    return jobs


# Add a full detail endpoint if the status one is too limited
@router.get("/{job_id}", response_model=WorkflowJobRead)
async def get_job_detail(
    job_id: int,
    user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[Session, Depends(get_session)],
):
    job = session.exec(
        select(WorkflowJob).where(WorkflowJob.id == job_id, WorkflowJob.user_id == user.id)
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/{job_id}/stream")
async def stream_job(job_id: int, user: Annotated[User, Depends(get_current_active_user)]):
    user_id = cast(int, user.id)

    async def event_generator():
        queue = get_job_queue(user_id, job_id)
        if not queue:
            yield {"event": "error", "data": "Stream not found or expired"}
            return

        try:
            while True:
                message = await queue.get()
                yield message

                # Check for terminal states to close the SSE connection
                is_status = message.get("event") == "status"
                is_terminal = message.get("data") in ["COMPLETED", "FAILED"]

                if (is_status and is_terminal) or message.get("event") == "error":
                    break
        finally:
            # Cleanup memory when client disconnects or job finishes
            if user_id in job_streams and job_id in job_streams[user_id]:
                del job_streams[user_id][job_id]
                if not job_streams[user_id]:
                    del job_streams[user_id]

    return EventSourceResponse(event_generator())


@router.get("/{job_id}/output", response_model=list[dict])
async def list_job_outputs(
    job_id: int,
    user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[Session, Depends(get_session)],
):
    """Lists files generated ONLY in the job's output sub-directory."""
    job = session.exec(
        select(WorkflowJob).where(WorkflowJob.id == job_id, WorkflowJob.user_id == user.id)
    ).first()

    if not job or not job.workspace_path:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Point specifically to the 'output' directory
    output_dir = Path(job.workspace_path) / "output"

    if not output_dir.exists() or not output_dir.is_dir():
        return []

    results = []
    # Using rglob("*") is often cleaner than os.walk for simple path filtering
    for full_path in output_dir.rglob("*"):
        if full_path.is_file():
            rel_path = full_path.relative_to(output_dir)
            results.append(
                {"name": full_path.name, "path": str(rel_path), "size": full_path.stat().st_size}
            )
    return results


@router.get("/{job_id}/output/download/{file_path:path}")
async def download_job_output(
    job_id: int,
    file_path: str,
    user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[Session, Depends(get_session)],
):
    """Downloads a file, strictly restricted to the 'output' sub-directory."""
    job = session.exec(
        select(WorkflowJob).where(WorkflowJob.id == job_id, WorkflowJob.user_id == user.id)
    ).first()

    if not job or not job.workspace_path:
        raise HTTPException(status_code=404, detail="Job or workspace not found")

    # Set base specifically to output folder
    output_base = (Path(job.workspace_path) / "output").resolve()
    target_file = (output_base / file_path).resolve()

    # Security: Ensure target is strictly inside output_base
    if not str(target_file).startswith(str(output_base)):
        raise HTTPException(status_code=403, detail="Access denied: outside of output scope")

    if not target_file.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(target_file, filename=target_file.name)
