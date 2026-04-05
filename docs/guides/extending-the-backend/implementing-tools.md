# Implementing a New Tool

This guide explains how to implement a new tool in `myproject-tools` and register it with the global `ToolRegistry`.

For the tool system's architecture, see [tool-architecture.md](../../architecture/tools-and-extensibility/tool-architecture.md).

---

## Overview

Tools extend the agent's capabilities. Each tool:

1. Inherits from `BaseTool` ABC
2. Defines `name`, `description`, and `parameters` as class attributes
3. Implements `async run()` returning a `ToolResult`
4. Registers itself with the `ToolRegistry`

---

## Step 1: Define the Tool Class

Choose a clear `name` and a descriptive `description` (the LLM uses this to decide when to call the tool). Define `parameters` as a JSON Schema object:

```python
from myproject_tools.base import BaseTool
from myproject_tools.schema import ToolResult

class MyTool(BaseTool):
    name = "my_custom_tool"
    description = "Searches the user's knowledge base for relevant notes."
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "The search query"},
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results",
                "default": 5,
            },
        },
        "required": ["query"],
    }

    async def run(
        self, working_directory: Path, query: str, max_results: int = 5, **kwargs
    ) -> ToolResult:
        ...
```

## Step 2: Design Output Channels

Decide where the tool's output goes:

| Channel | Use when |
|---|---|
| `tool_response` | Short confirmations, errors, summaries (goes to chat history) |
| `results_to_add_to_clipboard` | Large text the agent should read without cluttering context |
| `files_to_add_to_clipboard` | Files the agent should inspect on the next turn |
| `entities_to_track` | Productivity items (tasks, projects, journals) the agent should monitor |

## Step 3: Implement the Run Method

```python
async def run(
    self, working_directory: Path, query: str, max_results: int = 5, **kwargs
) -> ToolResult:
    # Always validate paths first
    safe_path = self._validate_path(working_directory, "kb_index.json", must_exist=True)

    results = await self._search_index(safe_path, query, max_results)

    return ToolResult(
        status="success",
        tool_response=f"Found {len(results)} notes matching '{query}'",
        results_to_add_to_clipboard=[json.dumps(results, indent=2)],
    )
```

**Key rules:**
- **Async only** — use `asyncio.to_thread()` for blocking I/O
- **Always validate paths** — call `_validate_path()` before any file operation
- **Return `ToolResult`**, never raise — errors return `status="error"` with a message

## Step 4: Register the Tool

In `myproject-tools/src/myproject_tools/registry.py`:

```python
from .my_tool import MyTool

tool_registry.register("my_custom_tool", MyTool)
```

## Path Validation Reference

Tools that access the filesystem must validate paths against the sandbox:

```python
self._validate_path(
    working_directory,    # Sandbox root
    path_str,              # Path provided by the agent
    must_exist=True,       # Check file exists
    should_be_dir=False,   # Must be a directory
    should_be_file=False,  # Must be a file
)
```

This blocks `../etc/passwd` traversal attacks. It raises `ValueError` if the path escapes the sandbox — the agent loop catches this and returns it as an error `ToolResult`.
