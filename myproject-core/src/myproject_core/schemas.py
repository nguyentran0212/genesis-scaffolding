from pydantic import BaseModel


class LLMProvider(BaseModel):
    base_url: str
    api_key: str


class LLMModel(BaseModel):
    provider: LLMProvider
    model: str
