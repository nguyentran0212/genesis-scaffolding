from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from .configs import settings
from .schemas import AgentClipboard


class AgentMemory:
    def __init__(
        self, messages: list[Any] | None = None, agent_clipboard: AgentClipboard | None = None
    ) -> None:
        self.messages = messages if messages else []
        self.agent_clipboard = agent_clipboard if agent_clipboard else AgentClipboard()

    def append_memory(self, message: Any):
        self.messages.append(message)

    def get_messages(self) -> list[Any]:
        """Returns the raw message history."""
        return self.messages

    def reset_memory(self):
        self.messages = []
        self.agent_clipboard = AgentClipboard()

    def forget(self):
        self.agent_clipboard.reduce_ttl()
        self.agent_clipboard.remove_expired_items()

    def get_clipboard_message(self) -> dict[str, str]:
        """
        Formats the clipboard as a system message.
        This is ephemeral and should not be stored in self.messages.
        """
        timezone = settings.server.timezone
        now = datetime.now(ZoneInfo(timezone))
        content = (
            "## CURRENT CLIPBOARD\n"
            "The following information is your current working context.\n\n"
            f"{self.agent_clipboard.render_to_markdown()}\n\n\n====="
            "## CURRENT DATE TIME\n"
            f"{now.strftime('%Y-%m-%d %H:%M:%S %Z %z')}\n\n====="
        )
        return {"role": "system", "content": content}

    def add_file_to_clipboard(self, file_path: Path, content: str):
        """Adds or updates a file in the clipboard."""
        self.agent_clipboard.add_file_to_clipboard(file_path=file_path, content=content)

    def add_tool_results_to_clipboard(self, tool_name: str, tool_call_id: str, results: list[str]):
        """Adds tool results to clipboard"""
        self.agent_clipboard.add_tool_result_to_clipboard(
            tool_name=tool_name, tool_call_id=tool_call_id, tool_call_results=results
        )

    def estimate_total_tokens(self) -> int:
        """
        Estimates the total token count of history + current clipboard.
        Uses a 4-char-per-token heuristic.
        """
        # 1. Calculate History length
        history_text = "".join([m["content"] for m in self.messages])

        # 2. Calculate Clipboard length (as it will be rendered)
        clipboard_text = self.agent_clipboard.render_to_markdown()

        total_chars = len(history_text) + len(clipboard_text)
        return total_chars // 4
