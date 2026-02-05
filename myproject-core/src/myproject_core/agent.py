import asyncio

from myproject_core.schemas import LLMModel, LLMProvider

from .agent_memory import AgentMemory
from .llm import get_llm_response
from .configs import settings

from typing import Any


class Agent:
    def __init__(self, llm: LLMModel, memory: AgentMemory | None = None) -> None:
        self.llm = llm
        if memory:
            self.memory = memory
        else:
            self.memory = AgentMemory([])

    async def step(self, input: Any):
        self.memory.append_memory(message=input)
        response = await get_llm_response(
            llm_model=self.llm, messages=self.memory.get_messages()
        )
        self.memory.append_memory(message=response)


if __name__ == "__main__":
    llm_provider = LLMProvider(
        base_url=settings.llm.base_url, api_key=settings.llm.api_key
    )
    llm_model = LLMModel(provider=llm_provider, model=settings.llm.model)
    agent = Agent(llm=llm_model)
    asyncio.run(agent.step({"content": "Hello, how are you?", "role": "user"}))
    messages = agent.memory.get_messages()
    print(messages)
