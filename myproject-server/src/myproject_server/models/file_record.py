from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .user import User


class FileRecordBase(SQLModel):
    filename: str = Field(index=True)
    # Physical location relative to the project root or inbox_directory
    file_path: str
    # Logical location relative to the user's sandbox root (e.g., "docs/notes.txt")
    relative_path: str = Field(index=True)
    # The directory part of the relative path (e.g., "docs") for fast filtering
    folder: str = Field(default=".", index=True)

    mime_type: str | None = None
    size: int | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class FileRecord(FileRecordBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    user: "User" = Relationship()
