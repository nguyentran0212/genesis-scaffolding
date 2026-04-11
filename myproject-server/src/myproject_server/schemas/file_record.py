from pydantic import BaseModel


class SandboxFileRead(BaseModel):
    """API response schema for file read operations.
    Replicates the fields from SandboxFileInfo in myproject_core.schemas.
    """

    relative_path: str
    name: str
    is_dir: bool = False
    size: int | None = None
    mime_type: str | None = None
    mtime: float | None = None
    created_at: str | None = None


class FileUploadResponse(BaseModel):
    message: str
    file: SandboxFileRead
