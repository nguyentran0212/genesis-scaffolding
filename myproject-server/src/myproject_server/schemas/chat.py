from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class ChatSessionCreate(BaseModel):
    agent_id: str
    title: Optional[str] = "New Chat"


class ChatSessionRead(BaseModel):
    id: int
    agent_id: str
    title: str
    is_running: bool  # Critical for the frontend "Send" button
    created_at: datetime
    updated_at: datetime


class ChatMessageRead(BaseModel):
    id: int
    payload: dict[str, Any]  # The raw JSON from the core
    created_at: datetime


class ChatHistoryRead(BaseModel):
    session: ChatSessionRead
    messages: list[ChatMessageRead]
