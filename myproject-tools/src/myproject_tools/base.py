from abc import ABC, abstractmethod
from typing import Any

from .schema import ToolResult


class BaseTool(ABC):
    # We define these as class attributes with type hints
    # Subclasses can now simple assign 'name = "..."'
    name: str
    description: str
    parameters: dict[str, Any]

    @abstractmethod
    async def run(self, *args: Any, **kwargs: Any) -> ToolResult:
        """Execute logic and return a ToolResult data object."""
        pass

    def to_llm_schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }
