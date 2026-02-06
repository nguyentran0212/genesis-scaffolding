from typing import Awaitable, Callable

from pydantic import BaseModel


class LLMProvider(BaseModel):
    base_url: str
    api_key: str


class LLMModel(BaseModel):
    provider: LLMProvider
    model: str


class LLMResponse(BaseModel):
    content: str
    reasoning_content: str


# This type hint says: "A function that takes a string and returns a coroutine"
StreamCallback = Callable[[str], Awaitable[None]]
