from typing import Any

from .base import BaseTool
from .schema import ToolResult


class MockTestTool(BaseTool):
    name = "test_tool"
    description = "A tool for testing the agent's ability to handle success and failure."
    parameters = {
        "type": "object",
        "properties": {"input_text": {"type": "string"}, "should_fail": {"type": "boolean"}},
    }

    async def run(self, input_text: str, should_fail: bool = False, **kwargs: Any) -> ToolResult:
        if should_fail:
            # Test exception catching
            raise Exception(f"Simulated crash with input: {input_text}")

        return ToolResult(
            content="Processed input text successfully and added to the clipboard",
            status="success",
            add_to_clipboard=True,
        )
