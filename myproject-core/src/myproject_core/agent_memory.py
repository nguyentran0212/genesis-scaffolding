from typing import Any


class AgentMemory:
    def __init__(self, messages: list[Any] | None) -> None:
        if messages:
            self.messages = messages
        else:
            self.messages = []

    def append_memory(self, message: Any):
        self.messages.append(message)

    def reset_memory(self):
        self.messages = []

    def get_messages(self) -> list[Any]:
        return self.messages

    def compress_memory(self):
        """
        To be implemented later
        """
        pass
