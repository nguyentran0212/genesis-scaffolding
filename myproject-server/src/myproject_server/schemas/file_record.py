from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FileRecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    relative_path: str  # e.g., "docs/proposals/draft.pdf"
    folder: str  # e.g., "docs/proposals"
    mime_type: str | None
    size: int | None
    created_at: datetime


class FileUploadResponse(BaseModel):
    message: str
    file: FileRecordRead
