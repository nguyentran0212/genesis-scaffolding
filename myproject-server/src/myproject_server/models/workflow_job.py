from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional

from sqlmodel import JSON, Column, Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .user import User
    from .workflow_schedule import WorkflowSchedule


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class WorkflowJobBase(SQLModel):
    workflow_id: str = Field(index=True)  # The manifest identifier
    status: JobStatus = Field(default=JobStatus.PENDING, index=True)

    # Store inputs and results as JSON
    inputs: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    result: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))

    # Keep the progress of steps
    step_status: dict[str, str] = Field(default_factory=dict, sa_column=Column(JSON))

    error_message: str | None = None
    workspace_path: str | None = None  # Path provided by WorkspaceManager

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class WorkflowJob(WorkflowJobBase, table=True):
    id: int | None = Field(default=None, primary_key=True)

    user_id: int = Field(foreign_key="user.id", index=True)
    user: "User" = Relationship()
    schedule_id: int | None = Field(default=None, foreign_key="workflowschedule.id", nullable=True)
    schedule: Optional["WorkflowSchedule"] = Relationship(back_populates="jobs")
