from typing import List

from pydantic import BaseModel


class AgentRead(BaseModel):
    name: str
    description: str
    interactive: bool
    allowed_tools: List[str]
    allowed_agents: List[str]
    # We include the model name but NOT the provider's API key
    model_name: str | None = None
