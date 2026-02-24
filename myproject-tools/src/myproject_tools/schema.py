from typing import Any, Optional

from pydantic import BaseModel


class ToolResult(BaseModel):
    content: str  # The main output or error message
    status: str  # "success" or "error"

    # Hints for the Core
    add_to_clipboard: bool = False
    file_path_hint: str | None = None  # e.g., "research_paper.md"

    # Any extra data the tool wants to pass back
    metadata: Optional[dict[str, Any]] = None
