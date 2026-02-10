import asyncio
from pathlib import Path
from typing import Literal

from .agent_memory import AgentMemory
from .configs import settings
from .llm import get_llm_response
from .schemas import AgentConfig, LLMModel, LLMProvider, StreamCallback
from .utils import streamcallback_simple_print


class Agent:
    def __init__(
        self,
        agent_config: AgentConfig,
        memory: AgentMemory | None = None,
        content_chunk_callbacks: list[StreamCallback] | None = None,
        reasoning_chunk_callbacks: list[StreamCallback] | None = None,
    ) -> None:
        self.agent_config = agent_config
        if not agent_config.llm_config:
            raise Exception(f"Agent {agent_config.name} does not have llm configuration.")
        self.llm = agent_config.llm_config
        system_prompt = agent_config.system_prompt
        self.memory = (
            memory
            if memory
            else AgentMemory(messages=[self._create_llm_message(role="system", content=system_prompt)])
        )
        self.stream = agent_config.interactive
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
        """
        Agent calls LLM to progress to the next step
        The clipboard is injected to message list to send to LLM to provid the context
        Then, clipboard is removed so that it does not inflate the message history
        """
        # Store the user's raw input in permanent memory
        user_msg = self._create_llm_message(role="user", content=input)
        self.memory.append_memory(user_msg)

        # Build the ephemeral payload for the LLM
        # Current memory.messages is [..., UserMsg]
        history = self.memory.get_messages()

        # We want to insert the clipboard right before the last message
        past_history = history[:-1]
        latest_query = history[-1:]
        clipboard_context = [self.memory.get_clipboard_message()]

        # print(clipboard_context)

        full_payload = past_history + clipboard_context + latest_query
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
            messages=full_payload,
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

        return llm_response.content

    async def add_file(self, file_path: Path):
        """Method for external workflows to feed files to the agent."""
        if not file_path.exists():
            raise FileNotFoundError(f"Workflow provided invalid path: {file_path}")

        # In a real scenario, you'd handle different encodings/extensions here
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.memory.add_file_to_clipboard(file_path, content)


async def main():
    llm_provider = LLMProvider(base_url=settings.llm.base_url, api_key=settings.llm.api_key)
    llm_model = LLMModel(provider=llm_provider, model=settings.llm.model)
    agent_config = AgentConfig(name="my-test-agent", llm_config=llm_model)
    print(agent_config)
    agent = Agent(
        agent_config=agent_config,
        content_chunk_callbacks=[streamcallback_simple_print],
        reasoning_chunk_callbacks=[streamcallback_simple_print],
    )

    print(f"Turn 1:\n{await agent.step('hello, how are you?')}\n-----")

    await agent.add_file(Path(__file__).resolve())

    print(f"Turn 2:\n{await agent.step('Can you explain to me the file in the clipboard?')}\n-----")

    messages = agent.memory.get_messages()
    print(f"\n\nAll of the messages:\n{messages}")


if __name__ == "__main__":
    asyncio.run(main())
