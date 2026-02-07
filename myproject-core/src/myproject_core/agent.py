import asyncio
from typing import Literal

from myproject_core.schemas import LLMModel, LLMProvider

from .agent_memory import AgentMemory
from .configs import settings
from .llm import get_llm_response
from .schemas import StreamCallback
from .utils import streamcallback_simple_print


class Agent:
    def __init__(
        self,
        llm: LLMModel,
        stream: bool = False,
        memory: AgentMemory | None = None,
        content_chunk_callbacks: list[StreamCallback] | None = None,
        reasoning_chunk_callbacks: list[StreamCallback] | None = None,
    ) -> None:
        self.llm = llm
        self.stream = stream
        self.memory = memory if memory else AgentMemory()
        self.content_chunk_callbacks = content_chunk_callbacks
        self.reasoning_chunk_callbacks = reasoning_chunk_callbacks

    def _create_llm_message(
        self,
        role: Literal["user", "assistant", "system"],
        content: str,
        reasoning_content: str | None = None,
    ):
        llm_message = {"role": role, "content": content}
        if reasoning_content:
            llm_message["reasoning_content"] = reasoning_content

        return llm_message

    async def step(
        self,
        input: str,
        stream: bool | None = None,
        content_chunk_callbacks: list[StreamCallback] | None = None,
        reasoning_chunk_callbacks: list[StreamCallback] | None = None,
    ):
        # Create and add user's message to the memory of the agent
        self.memory.append_memory(message=self._create_llm_message(role="user", content=input))
        # Call LLM for response
        # Allow caller to override the streaming and callbacks for displaying chunks, but default to the callbacks aassigned to the agent at creation time
        stream = stream if stream is not None else self.stream
        content_chunk_callbacks = (
            content_chunk_callbacks if content_chunk_callbacks else self.content_chunk_callbacks
        )
        reasoning_chunk_callbacks = (
            reasoning_chunk_callbacks if reasoning_chunk_callbacks else self.reasoning_chunk_callbacks
        )
        llm_response = await get_llm_response(
            llm_model=self.llm,
            messages=self.memory.get_messages(),
            stream=stream,
            content_chunk_callbacks=content_chunk_callbacks,
            reasoning_chunk_callbacks=reasoning_chunk_callbacks,
        )
        # Add response to memory
        self.memory.append_memory(
            self._create_llm_message(
                role="assistant",
                content=llm_response.content,
                reasoning_content=llm_response.reasoning_content,
            )
        )
        # Return the latest response from the model as next step
        return self.memory.get_messages()[-1]["content"]


async def main():
    llm_provider = LLMProvider(base_url=settings.llm.base_url, api_key=settings.llm.api_key)
    llm_model = LLMModel(provider=llm_provider, model=settings.llm.model)
    agent = Agent(
        llm=llm_model,
        stream=True,
        content_chunk_callbacks=[streamcallback_simple_print],
        reasoning_chunk_callbacks=[streamcallback_simple_print],
    )

    print(f"Turn 1:\n{await agent.step('hello, how are you?')}\n-----")
    print(f"Turn 2:\n{await agent.step('What are your capabilities?')}\n-----")

    messages = agent.memory.get_messages()
    print(f"\n\nAll of the messages:\n{messages}")


if __name__ == "__main__":
    asyncio.run(main())
