from .arxiv import ArxivPaperDetailTool, ArxivSearchTool
from .base import BaseTool
from .test_tools import MockTestTool


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, type[BaseTool]] = {}

    def register(self, name: str, tool_class: type[BaseTool]):
        """Register a tool instance."""
        # hacky implementation for now to overwrite the tool name
        # The goal here is so that the dictionary key matches the name define in class
        tool_class.name = name
        self._tools[name] = tool_class

    def get_tool(self, name: str) -> BaseTool | None:
        """Look up a tool by name."""
        tool_class = self._tools.get(name)
        if not tool_class:
            return None
        return tool_class()

    def get_all_tool_names(self) -> list[str]:
        return list(self._tools.keys())


# Global registry instance
tool_registry = ToolRegistry()

tool_registry.register("test_tool", MockTestTool)
tool_registry.register("arxiv_paper_detail_tool", ArxivPaperDetailTool)
tool_registry.register("arxiv_paper_search_tool", ArxivSearchTool)


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
