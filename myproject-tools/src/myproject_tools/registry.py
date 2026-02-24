from .base import BaseTool
from .test_tools import MockTestTool


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool_instance: BaseTool):
        """Register a tool instance."""
        self._tools[tool_instance.name] = tool_instance

    def get_tool(self, name: str) -> BaseTool | None:
        """Look up a tool by name."""
        return self._tools.get(name)

    def get_all_tool_names(self) -> list[str]:
        return list(self._tools.keys())


# Global registry instance
tool_registry = ToolRegistry()

tool_registry.register(MockTestTool())


def main():
    print(tool_registry.get_all_tool_names())
    for tool_name in tool_registry.get_all_tool_names():
        tool = tool_registry.get_tool(tool_name)
        if tool:
            print(tool.name)
            print(tool.description)
            print(tool.parameters)


if __name__ == "__main__":
    main()
