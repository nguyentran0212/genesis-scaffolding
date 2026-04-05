# Tool Architecture

## Overview

The tool system extends the agent's capabilities through a **BaseTool ABC** in `myproject-tools` and a **global ToolRegistry** that maps tool names to tool classes. The agent loop uses the registry to convert tool classes to LLM function-calling schemas, execute tools, and route results back.

```
ToolRegistry (myproject_tools/registry.py)
└── tool_registry.register("tool_name", ToolClass)
       └── tool_registry.get_tool("tool_name") → BaseTool instance

Agent Loop
├── tool_registry.get_all_tool_names() → list of schema dicts → LLM
├── tool_registry.get_tool(name) → execute tool.run()
└── ToolResult (three channels) → agent loop processes each
```

---

## BaseTool ABC

**File:** `myproject-tools/src/myproject_tools/base.py`

```python
class BaseTool(ABC):
    name: str
    description: str
    parameters: dict[str, Any]

    @abstractmethod
    async def run(self, working_directory: Path, *args: Any, **kwargs: Any) -> ToolResult:
        ...

    def to_llm_schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }
```

Subclasses assign `name`, `description`, and `parameters` as class attributes. The `parameters` dict follows the OpenAI function-calling schema format (JSON Schema `type: "object"` with `properties`).

### Path Validation

`_validate_path()` is a built-in utility for file-manipulating tools:

```python
def _validate_path(self, working_directory: Path, path_str: str,
                  must_exist=True, should_be_dir=False, should_be_file=False) -> Path:
```

It resolves the path relative to `working_directory` and enforces:
1. **No escape** — resolved path must be inside `working_directory` (blocks `../etc/passwd`)
2. **Existence** — optionally checks the path exists
3. **Type** — optionally checks it is a file or directory

This is the enforcement mechanism for the **sandbox working directory contract** (see below).

---

## ToolResult Schema

**File:** `myproject-tools/src/myproject_tools/schema.py`

```python
class ToolResult(BaseModel):
    status: Literal["success", "error"]
    tool_response: str                        # Text sent to LLM chat history
    results_to_add_to_clipboard: list[str]|None = None  # Text added to clipboard
    files_to_add_to_clipboard: list[Path] = []           # Files read into clipboard
    entities_to_track: list[TrackedEntity] = []          # DB entities to pin
```

### The Three Channels

| Channel | Purpose |
|---|---|
| `tool_response` | Primary output/error text; goes directly into the LLM's next input |
| `results_to_add_to_clipboard` | Large text content separated from chat history to preserve context window |
| `files_to_add_to_clipboard` | Files read by the agent on the next turn (e.g., output of a previous step) |
| `entities_to_track` | Database entities (tasks, projects, journals) pinned to clipboard for live-sync |

### TrackedEntity

```python
class TrackedEntity(BaseModel):
    item_type: Literal["task", "project", "journal", "memory_event", "memory_topic"]
    item_id: int
    resolution: Literal["summary", "detail"] = "summary"
    ttl: int = 10
```

Agents pin a productivity entity to the clipboard. On each turn, the clipboard live-syncs the entity data from the DB — so if a task is completed via another tool, the agent sees the updated state on the next turn without re-reading.

---

## ToolRegistry

**File:** `myproject-tools/src/myproject_tools/registry.py`

```python
class ToolRegistry:
    def register(self, name: str, tool_class: type[BaseTool]): ...
    def get_tool(self, name: str) -> BaseTool | None: ...
    def get_all_tool_names(self) -> list[str]: ...
```

The registry maps **string names** to tool classes. At import time, all built-in tools register themselves:

```python
tool_registry = ToolRegistry()

tool_registry.register("test_tool", MockTestTool)
tool_registry.register("get_arxiv_paper_detail", ArxivPaperDetailTool)
tool_registry.register("search_arxiv_paper", ArxivSearchTool)
tool_registry.register("convert_pdf_to_markdown_tool", PdfToMarkdownTool)
tool_registry.register("fetch_rss_feed", RssFetchTool)
tool_registry.register("fetch_web_page", WebPageFetchTool)
tool_registry.register("search_web", WebSearchTool)
tool_registry.register("search_news", NewsSearchTool)
tool_registry.register("list_files", ListFilesTool)
tool_registry.register("read_file", ReadFileTool)
tool_registry.register("write_file", WriteFileTool)
tool_registry.register("edit_file", EditFileTool)
tool_registry.register("find_files", FindFilesTool)
tool_registry.register("delete_file", DeleteFileTool)
tool_registry.register("move_or_rename_file", MoveFileTool)
tool_registry.register("search_file_content", SearchFileContentTool)
tool_registry.register("search_tasks", SearchTasksTool)
tool_registry.register("read_task", ReadTaskTool)
tool_registry.register("search_projects", SearchProjectsTool)
tool_registry.register("read_project", ReadProjectTool)
tool_registry.register("search_journals", SearchJournalsTool)
tool_registry.register("read_journal", ReadJournalTool)
tool_registry.register("create_task", CreateTaskTool)
tool_registry.register("create_project", CreateProjectTool)
tool_registry.register("create_journal", CreateJournalTool)
tool_registry.register("update_tasks", UpdateTasksTool)
tool_registry.register("update_project", UpdateProjectTool)
tool_registry.register("edit_journal", EditJournalTool)
tool_registry.register("remember_this", RememberThisTool)
tool_registry.register("search_memories", SearchMemoriesTool)
tool_registry.register("list_memories", ListMemoriesTool)
tool_registry.register("get_memory", GetMemoryTool)
tool_registry.register("update_memory", UpdateMemoryTool)
tool_registry.register("delete_memory", DeleteMemoryTool)
tool_registry.register("rebuild_fts_index", RebuildFtsIndexTool)
tool_registry.register("compute_date_range", ComputeDateRangeTool)
```

**30 built-in tools** across five categories: file ops, web, productivity, memory, and utility.

---

## Sandbox Working Directory Contract

The agent passes a `working_directory: Path` to every tool invocation. Tools MUST treat this as the root of their accessible filesystem:

1. **Every path operation** should be resolved relative to `working_directory`
2. **Path validation** (`_validate_path()`) MUST be called before any file access to prevent traversal attacks
3. **No absolute paths** are permitted from the agent; if the agent passes an absolute path, `_validate_path()` resolves it and rejects it if it escapes the sandbox

The sandbox root is set by the `WorkspaceManager` or the user's inbox directory (from their config). For interactive chat sessions, it is the user's `working_directory`. For workflow jobs, it is the job's `JobContext.root` with subdirectories `input/`, `internal/`, and `output/`.

---

## Workflow Tool Calls

Tools are also used inside workflow tasks. The workflow engine uses `ToolRegistry.get_tool(name)` to instantiate tools and call them with a workflow-specific `working_directory` (the `JobContext.root` of the active job).

For step-by-step instructions on implementing a new tool, see [implementing-tools.md](../../guides/extending-the-backend/implementing-tools.md).
