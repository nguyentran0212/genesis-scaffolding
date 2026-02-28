import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from myproject_tools.pdf import convert_pdf_to_markdown
from myproject_tools.registry import tool_registry
from myproject_tools.schema import ToolResult

from .agent_memory import AgentMemory
from .configs import settings
from .llm import get_llm_response
from .schemas import AgentConfig, LLMModel, LLMProvider, StreamCallback, ToolCallback
from .utils import streamcallback_simple_print

SYSTEM_PROMPT_PREFIX = """
# GENERAL INSTRUCTION

You need to follow the role and specific instructions described later in this message to accomplish your goal of supporting me (the user).

You have access to a clipboard that stores relevant data in this session:
- content of files you read or provided to you
- results of your tool calls 
- your to-do list

This clipboard would be dynamically updated and provided to you after you finish calling tool and before any message from me, the user. 

After successful tool call, such as reading a file or fetching a web page, you would usually receive a response from tool to notify you where the retrieved content can be found.
the retrieved content is usually added to the clipboard. In this case, the tool call has completed.

-----

# ROLE DESCRIPTION AND INSTRUCTIONS

"""


class Agent:
    def __init__(
        self,
        agent_config: AgentConfig,
        memory: AgentMemory | None = None,
        working_directory: Path | None = None,
        content_chunk_callbacks: list[StreamCallback] | None = None,
        reasoning_chunk_callbacks: list[StreamCallback] | None = None,
    ) -> None:
        self.agent_config = agent_config
        if not agent_config.llm_config:
            raise Exception(f"Agent {agent_config.name} does not have llm configuration.")

        self.llm = agent_config.llm_config

        system_prompt = SYSTEM_PROMPT_PREFIX + agent_config.system_prompt
        self.memory = (
            memory
            if memory
            else AgentMemory(messages=[self._create_llm_message(role="system", content=system_prompt)])
        )

        self.stream = agent_config.interactive
        self.content_chunk_callbacks = content_chunk_callbacks
        self.reasoning_chunk_callbacks = reasoning_chunk_callbacks

        self.working_directory = working_directory
        if working_directory and not working_directory.exists():
            raise Exception(
                f"Agent {agent_config.name} was given a non-existent working directory: {working_directory}"
            )

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

    def _get_tool_definitions(self) -> list[dict]:
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

    async def _execute_tool_and_format(self, tool_id: str, name: str, args: dict, working_directory: Path):
        """Internal helper to run the tool and format the message for the LLM."""
        # 1. Look up tool
        tool = next((t for t in self.tools if t.name == name), None)

        try:
            if not tool:
                result_str = f"Error: Tool {name} not found."
            else:
                # Execute (Pure data generation)
                result: ToolResult = await tool.run(working_directory=working_directory, **args)

                # Side Effect: Add files to clipboard
                if result.status == "success" and result.files_to_add_to_clipboard:
                    for file_path in result.files_to_add_to_clipboard:
                        await self.add_file(file_path=file_path, working_directory=working_directory)

                # Side Effect: Add tool results to clipboard
                if result.status == "success" and result.results_to_add_to_clipboard:
                    self.memory.add_tool_results_to_clipboard(
                        tool_name=name, tool_call_id=tool_id, results=result.results_to_add_to_clipboard
                    )

                result_str = result.tool_response
        except Exception as e:
            # Uncaught error. This really should not happen as it messes up the agent
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

    def _get_current_working_directory(self, working_directory: Path | None):
        current_working_directory = working_directory or self.working_directory
        if not current_working_directory:
            raise Exception(
                f"Failed to call agent {self.agent_config.name}: the agent was not created with a working directory, and none was given when calling step()"
            )
        return current_working_directory

    async def step(
        self,
        input: str,
        working_directory: Path | None = None,
        stream: bool | None = None,
        content_chunk_callbacks: list[StreamCallback] | None = None,
        reasoning_chunk_callbacks: list[StreamCallback] | None = None,
        tool_start_callback: list[ToolCallback] | None = None,
        tool_result_callback: list[ToolCallback] | None = None,
        debug=False,
    ):
        """
        Agent calls LLM to progress to the next step
        The clipboard is injected to message list to send to LLM to provid the context
        Then, clipboard is removed so that it does not inflate the message history
        The agent would loop until max number of turn of until no more tool calls are detected.
        """

        # Fail fast if there is no working directory
        current_working_directory = self._get_current_working_directory(working_directory)

        # Add user message to memory
        self.memory.append_memory(self._create_llm_message(role="user", content=input))

        # Reduce ttl and remove any expire item from memory to save space
        self.memory.forget()

        # Remove the deleted files from the clipboard
        self.memory.remove_deleted_files()

        debug = True
        if debug:
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

            if debug:
                self._log_debug_messages(full_payload, turn)
            llm_response = await get_llm_response(
                llm_model=self.llm,
                messages=full_payload,
                stream=stream if stream is not None else self.stream,
                content_chunk_callbacks=content_chunk_callbacks,
                reasoning_chunk_callbacks=reasoning_chunk_callbacks,
                tools=self._get_tool_definitions() if self.tools else None,
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
                # Call back to notify tool call starting
                if tool_start_callback:
                    tool_start_cb = [cb(tc.function_name, args) for cb in tool_start_callback]
                    await asyncio.gather(*tool_start_cb)

                tool_tasks.append(
                    self._execute_tool_and_format(tc.id, tc.function_name, args, current_working_directory)
                )

            # Wait for all tool side-effects to finish
            tool_results = await asyncio.gather(*tool_tasks)

            # Add results to history and LOOP BACK
            for res_msg in tool_results:
                self.memory.append_memory(res_msg)
                # Call back to notify tool call results
                if tool_result_callback:
                    tool_start_cb = [
                        cb(res_msg["name"], {"result": res_msg["content"]}) for cb in tool_result_callback
                    ]
                    await asyncio.gather(*tool_start_cb)

    async def add_file(self, file_path: Path, working_directory: Path | None = None):
        """Method for external workflows to feed files to the agent."""

        # 1. Path Validation
        current_working_directory = self._get_current_working_directory(working_directory)
        resolved_path = file_path.resolve()

        if not resolved_path.is_relative_to(current_working_directory.resolve()):
            raise ValueError(f"Security Alert: Path {file_path} is outside of {current_working_directory}")

        if not resolved_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # 2. Determine File Type
        extension = resolved_path.suffix.lower()

        content = ""
        safe_file_path = resolved_path.relative_to(current_working_directory)
        extension = resolved_path.suffix.lower()

        # 1. Handle Known Non-Text Formats first
        if extension == ".pdf":
            return await asyncio.to_thread(
                convert_pdf_to_markdown, pdf_path=resolved_path, prune_references=True
            )

        # List of extensions to explicitly ignore (binaries/assets)
        # This prevents wasting IO on large images or compiled files
        BINARY_EXTENSIONS = {
            ".exe",
            ".bin",
            ".pyc",
            ".o",
            ".obj",
            ".dll",
            ".so",
            ".dylib",
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".bmp",
            ".ico",
            ".webp",
            ".mp3",
            ".mp4",
            ".wav",
            ".avi",
            ".mov",
            ".zip",
            ".tar",
            ".gz",
            ".7z",
            ".docx",
            ".xlsx",
            ".pptx",
            ".sqlite",
            ".db",
        }

        if extension in BINARY_EXTENSIONS:
            raise ValueError(f"Unsupported binary file type: {extension}")

        # 2. Heuristic: Check if the file is binary or text
        def is_text_and_read():
            # Check first 1024 bytes for null character
            with open(resolved_path, "rb") as f:
                chunk = f.read(1024)
                if b"\0" in chunk:
                    return None  # It's a binary file

            # If no null byte, attempt to read as text
            try:
                with open(resolved_path, "r", encoding="utf-8", errors="replace") as f:
                    return f.read()
            except Exception:
                return None

        content = await asyncio.to_thread(is_text_and_read)
        if content is None:
            raise ValueError(f"File {resolved_path.name} appears to be binary or unreadable.")

        # 4. Add to Memory
        self.memory.add_file_to_clipboard(safe_file_path, content)

    async def remove_files(self, path: Path, working_directory: Path | None = None) -> list[Path]:
        """
        Method for external workflows to remove files from the agent's clipboard
        Return a list of Path of files removed
        """

        # Path Validation
        current_working_directory = self._get_current_working_directory(working_directory)
        resolved_path = path.resolve()

        if not resolved_path.is_relative_to(current_working_directory.resolve()):
            raise ValueError(
                f"Security Alert: Path to remove {path} is outside of {current_working_directory}"
            )

        if not resolved_path.exists():
            raise FileNotFoundError(f"Given path not found: {path}")

        safe_path = resolved_path.relative_to(current_working_directory)

        if safe_path.is_file():
            if self.memory.remove_file_from_clipboard(safe_path):
                return [safe_path]

        if safe_path.is_dir():
            return self.memory.remove_dir_from_clipboard(safe_path)

        return []


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

    print(
        f"Turn 1:\n{await agent.step('hello, how are you?', working_directory=Path(__file__).parent)}\n-----"
    )

    await agent.add_file(Path(__file__).resolve())

    print(
        f"Turn 2:\n{await agent.step('Can you explain to me the file in the clipboard?', working_directory=Path(__file__).parent)}\n-----"
    )

    messages = agent.memory.get_messages()
    print(f"\n\nAll of the messages:\n{messages}")


if __name__ == "__main__":
    asyncio.run(main())
