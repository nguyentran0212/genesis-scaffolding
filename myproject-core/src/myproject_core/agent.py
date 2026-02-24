import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from myproject_tools.registry import tool_registry
from myproject_tools.schema import ToolResult

from .agent_memory import AgentMemory
from .configs import settings
from .llm import get_llm_response
from .schemas import AgentConfig, LLMModel, LLMProvider, StreamCallback, ToolCallback
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

        self.tools: list[Any] = []  # This will hold the tool instances
        self._resolve_tools()

    def _resolve_tools(self):
        """
        Attempts to import the tool registry and look up tools
        defined in allowed_tools.
        """
        try:
            for tool_name in self.agent_config.allowed_tools:
                tool = tool_registry.get_tool(tool_name)
                if tool:
                    self.tools.append(tool)
                else:
                    # Silently ignore or log that a tool wasn't found
                    print(f"Warning: Tool '{tool_name}' not found in registry.")

        except ImportError:
            # If myproject_tools is not available, agent simply has no tools
            self.tools = []

    def get_tool_definitions(self) -> list[dict]:
        """Returns the JSON schemas for all resolved tools for the LLM call."""
        return [t.to_llm_schema() for t in self.tools]

    def _create_llm_message(
        self,
        role: Literal["user", "assistant", "system", "tool"],
        content: str,
        reasoning_content: str | None = None,
        tool_calls: list[dict[str, Any]] | None = None,  # Add this
        tool_call_id: str | None = None,  # Add this for tool responses
    ) -> dict[str, Any]:  # Explicitly return dict[str, Any]
        llm_message: dict[str, Any] = {"role": role, "content": content}

        if reasoning_content:
            llm_message["reasoning_content"] = reasoning_content
        if tool_calls:
            llm_message["tool_calls"] = tool_calls
        if tool_call_id:
            llm_message["tool_call_id"] = tool_call_id

        return llm_message

    async def _handle_tool_execution(self, tool_name: str, args: dict) -> str:
        tool = next((t for t in self.tools if t.name == tool_name), None)
        if not tool:
            return f"Error: Tool {tool_name} not found."

        try:
            result = await tool.run(**args)

            if result.status == "success" and result.add_to_clipboard:
                # We use the hint if provided, otherwise a default
                path = Path(result.file_path_hint or f"{tool_name}_output.txt")
                self.memory.add_file_to_clipboard(path, result.content)

                # What we tell the LLM (The "Receipt")
                return f"Success: Content from {tool_name} added to clipboard."

            # 4. Standard return if not meant for clipboard
            return result.content

        except Exception as e:
            # Catch the simulated crash from our Test Tool
            return f"Tool Execution Error ({tool_name}): {str(e)}"

    async def step(
        self,
        input: str,
        stream: bool | None = None,
        content_chunk_callbacks: list[StreamCallback] | None = None,
        reasoning_chunk_callbacks: list[StreamCallback] | None = None,
        tool_start_callback: list[ToolCallback] | None = None,
    ):
        """
        Agent calls LLM to progress to the next step
        The clipboard is injected to message list to send to LLM to provid the context
        Then, clipboard is removed so that it does not inflate the message history
        The agent would loop until max number of turn of until no more tool calls are detected.
        """
        # Add user message to memory
        self.memory.append_memory(self._create_llm_message(role="user", content=input))

        with open("debug_messages.json", "w") as f:
            f.write("")

        # Build the ephemeral payload for the LLM
        # Current memory.messages is [..., UserMsg]
        history = self.memory.get_messages()

        # We want to insert the clipboard right before the last message
        past_history = history[:-1]
        latest_query = history[-1:]
        clipboard_context = [self.memory.get_clipboard_message()]
        full_payload = []

        if latest_query[0]["role"] == "user":
            full_payload = past_history + clipboard_context + latest_query
        else:
            full_payload = history + clipboard_context

        # Start the tool call loop
        for turn in range(10):
            # We want to insert the clipboard right before the last message
            past_history = history[:-1]
            latest_query = history[-1:]
            clipboard_context = [self.memory.get_clipboard_message()]
            full_payload = []

            if latest_query[0]["role"] == "user":
                full_payload = past_history + clipboard_context + latest_query
            else:
                full_payload = history + clipboard_context
            # Call LLM for response
            # Allow caller to override the streaming and callbacks for displaying chunks, but default to the callbacks aassigned to the agent at creation time
            stream = stream if stream is not None else self.stream
            content_chunk_callbacks = (
                content_chunk_callbacks if content_chunk_callbacks else self.content_chunk_callbacks
            )
            reasoning_chunk_callbacks = (
                reasoning_chunk_callbacks if reasoning_chunk_callbacks else self.reasoning_chunk_callbacks
            )

            self._log_debug_messages(full_payload, turn)
            llm_response = await get_llm_response(
                llm_model=self.llm,
                messages=full_payload,
                stream=stream if stream is not None else self.stream,
                content_chunk_callbacks=content_chunk_callbacks,
                reasoning_chunk_callbacks=reasoning_chunk_callbacks,
                tools=self.get_tool_definitions() if self.tools else None,
            )

            # 4. Store Assistant Response in memory
            # If there are tool calls, LiteLLM/OpenAI requires they be stored in the history
            assistant_msg = self._create_llm_message(
                role="assistant",
                content=llm_response.content,
                reasoning_content=llm_response.reasoning_content,
            )
            if llm_response.tool_calls:
                # Convert our schema back to the format LiteLLM expects for history
                assistant_msg["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function_name, "arguments": tc.arguments},
                    }
                    for tc in llm_response.tool_calls
                ]

            self.memory.append_memory(assistant_msg)

            # 5. Check if we need to call tools
            if not llm_response.tool_calls:
                # No more tools? Return the final text
                return llm_response.content

            # 6. Execute Tools in Parallel
            tool_tasks = []
            for tc in llm_response.tool_calls:
                args = json.loads(tc.arguments)
                if tool_start_callback:
                    tool_start_cb = [cb(tc.function_name, args) for cb in tool_start_callback]
                    await asyncio.gather(*tool_start_cb)

                tool_tasks.append(self._execute_tool_and_format(tc.id, tc.function_name, args))

            # Wait for all tool side-effects to finish
            tool_results = await asyncio.gather(*tool_tasks)

            # Add results to history and LOOP BACK
            for res_msg in tool_results:
                self.memory.append_memory(res_msg)

    async def _execute_tool_and_format(self, tool_id: str, name: str, args: dict):
        """Internal helper to run the tool and format the message for the LLM."""
        # 1. Look up tool
        tool = next((t for t in self.tools if t.name == name), None)

        try:
            if not tool:
                result_str = f"Error: Tool {name} not found."
            else:
                # 2. Execute (Pure data generation)
                result: ToolResult = await tool.run(**args)

                # 3. Core Side Effect (The Clipboard)
                if result.status == "success" and result.add_to_clipboard:
                    path = Path(result.file_path_hint or f"{name}_output.txt")
                    self.memory.add_file_to_clipboard(path, result.content)
                    result_str = f"Success: Content from {name} added to clipboard."
                else:
                    result_str = result.content
        except Exception as e:
            result_str = f"Tool Execution Error: {str(e)}"

        # Return the 'tool' role message required by LLM history
        return {"role": "tool", "tool_call_id": tool_id, "name": name, "content": result_str}

    def _log_debug_messages(self, messages: list[dict], turn: int):
        """Dumps the current message stack to a local JSON file for debugging."""
        timestamp = datetime.now().strftime("%H-%M-%S")
        debug_file = Path("debug_messages.json")

        # We append to the file so we can see the history of turns
        with open(debug_file, "a", encoding="utf-8") as f:
            log_entry = {
                "timestamp": timestamp,
                "agent": self.agent_config.name,
                "turn": turn,
                "messages": messages,
            }
            f.write(json.dumps(log_entry, indent=2) + "\n\n" + "=" * 50 + "\n\n")

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
