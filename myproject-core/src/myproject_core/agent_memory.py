from pathlib import Path
from typing import Any

from .schemas import AgentClipboard, AgentClipboardFile


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

    def get_clipboard_message(self) -> dict[str, str]:
        """
        Formats the clipboard as a system message.
        This is ephemeral and should not be stored in self.messages.
        """
        content = (
            "## CURRENT CLIPBOARD\n"
            "The following information is your current working context. "
            "Use this to answer the user's latest request.\n\n"
            f"{self.agent_clipboard.render_to_markdown()}"
        )
        return {"role": "system", "content": content}

    def add_file_to_clipboard(self, file_path: Path, content: str):
        """Adds or updates a file in the clipboard."""
        # Remove existing version of the file if it exists to avoid duplicates
        self.agent_clipboard.accessed_files = [
            f for f in self.agent_clipboard.accessed_files if f.file_path != file_path
        ]

        new_file = AgentClipboardFile(file_path=file_path, file_content=content)
        self.agent_clipboard.accessed_files.append(new_file)

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
