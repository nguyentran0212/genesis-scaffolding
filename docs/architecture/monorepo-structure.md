# Monorepo Structure

## Overview

The project uses **uv workspaces** to manage a Python monorepo where multiple packages share a single virtual environment and lockfile. The workspace root is the repository root; each sub-package is an independent Python project that can import from other members.

```
genesis-scaffolding/          ← workspace root (uv workspace)
├── pyproject.toml            ← workspace config + root project
├── uv.lock                   ← single lockfile for all packages
├── .venv/                    ← single shared virtual environment
├── myproject-core/           ← shared library (agents, workflows, LLM, memory, config)
├── myproject-tools/          ← built-in tool implementations
├── myproject-cli/            ← Typer CLI entry point
├── myproject-tui/            ← Textual TUI (stub)
├── myproject-server/         ← FastAPI REST API
└── myproject-frontend/       ← NextJS frontend (separate repo structure)
```

---

## The Workspace Root

**File:** `pyproject.toml`

```toml
[tool.uv.workspace]
members = [
    "myproject-core",
    "myproject-cli",
    "myproject-tui",
    "myproject-server",
    "myproject-tools",
]
```

This tells uv which subdirectories are workspace members. Adding a new package means:
1. Creating the directory with its own `pyproject.toml`
2. Adding it to this `members` list
3. Running `uv sync`

---

## The Five Packages

### `myproject-core`

The shared logic package. No other package should depend on the server, CLI, or tools — only on this.

| Path | Purpose |
|---|---|
| `src/myproject_core/agent.py` | Agent class: step loop, tool execution, clipboard management |
| `src/myproject_core/agent_registry.py` | Loads agent markdown files, factory for Agent instances |
| `src/myproject_core/agent_memory.py` | In-memory message history + clipboard state per session |
| `src/myproject_core/clipboard.py` | TTL-based LRU clipboard with decay |
| `src/myproject_core/workflow_engine.py` | Workflow execution: step sequencing, callbacks, blackboard |
| `src/myproject_core/workflow_registry.py` | Loads workflow YAML manifests |
| `src/myproject_core/workspace.py` | Sandboxed filesystem for workflow jobs |
| `src/myproject_core/llm/` | Provider-agnostic LLM interface (`get_llm_response()`) |
| `src/myproject_core/prompts/` | Fragment-based system prompt assembly |
| `src/myproject_core/memory/` | EventLog + TopicalMemory models + service layer |
| `src/myproject_core/configs.py` | Three-layer config loading (env → YAML → user isolation) |
| `src/myproject_core/schemas.py` | Shared Pydantic models (LLMProvider, ToolCall, AgentClipboard, etc.) |

**Key constraint:** `myproject-core` has no dependencies on `myproject-server`, `myproject-cli`, or `myproject-tools`. It is the base layer.

### `myproject-tools`

Tool implementations that extend the agent's capabilities.

| Path | Purpose |
|---|---|
| `src/myproject_tools/base.py` | `BaseTool` ABC |
| `src/myproject_tools/registry.py` | Global `ToolRegistry` with 30 built-in tool registrations |
| `src/myproject_tools/schema.py` | `ToolResult` + `TrackedEntity` schemas |
| `src/myproject_tools/file.py` | File operation tools (read, write, edit, delete, search) |
| `src/myproject_tools/productivity_tools.py` | Task, Project, Journal CRUD tools |
| `src/myproject_tools/memory_tools.py` | EventLog and TopicalMemory tools |
| `src/myproject_tools/web_search.py` | Web search and news tools |
| `src/myproject_tools/web_fetch.py` | Web page fetch tool |
| `src/myproject_tools/arxiv.py` | ArXiv paper search and detail tools |
| `src/myproject_tools/pdf.py` | PDF to Markdown conversion tool |

**Depends on:** `myproject-core`

### `myproject-cli`

Typer-based CLI entry point.

| Path | Purpose |
|---|---|
| `src/myproject_cli/main.py` | `start()` function registered as `myproject` console script |

**Depends on:** `myproject-core`, `myproject-tools`

### `myproject-server`

FastAPI REST API with auth, SSE streaming, and scheduler.

| Path | Purpose |
|---|---|
| `src/myproject_server/main.py` | FastAPI app, lifespan, router registration |
| `src/myproject_server/dependencies.py` | Per-request DI: user, config, session, registries |
| `src/myproject_server/database.py` | System SQLite engine, `init_db()`, `seed_admin_user()` |
| `src/myproject_server/chat_manager.py` | `ChatManager` singleton, `ActiveRun` for SSE |
| `src/myproject_server/scheduler.py` | `SchedulerManager` wrapping APScheduler |
| `src/myproject_server/auth/` | JWT auth + Argon2id password hashing |
| `src/myproject_server/models/` | SQLModel table definitions |
| `src/myproject_server/schemas/` | Pydantic request/response schemas |
| `src/myproject_server/routers/` | API route modules (auth, chat, agents, workflows, etc.) |
| `src/myproject_server/utils/` | Config persistence, workflow job helpers, file utilities |

**Depends on:** `myproject-core`, `myproject-tools`

### `myproject-tui`

Textual TUI — currently a stub for future development.

**Depends on:** `myproject-core`

---

## Import Conventions

| Convention | Example |
|---|---|
| Package name (hyphens) | `myproject-core` in `pyproject.toml` |
| Import name (underscores) | `import myproject_core` in Python code |
| Always use underscores | Never `import myproject-core` |

```python
# Correct
from myproject_core.agent_registry import AgentRegistry
from myproject_core.configs import get_config

# Wrong — will fail
import myproject-core
```

---

## Dependency Management

### Adding a Package

```bash
# 1. Initialize
uv init --lib myproject-newpackage

# 2. Register in workspace members
# Edit pyproject.toml:
# [tool.uv.workspace]
# members = [..., "myproject-newpackage"]

# 3. Link internal dependencies
uv add --package myproject-newpackage myproject-core

# 4. Sync
uv sync
```

### Adding an External Dependency to a Package

```bash
# Adds httpx only to myproject-tools
uv add --package myproject-tools httpx

# Adds pytest as a dev dependency at root (affects all packages)
uv add --dev pytest
```

After any change, run `uv sync` to update `.venv` and `uv.lock`.

---

## Development Commands

| Command | Action |
|---|---|
| `make setup` | Install dependencies + git hooks |
| `make backend-format` | `ruff format` across all workspace members |
| `make backend-lint` | `ruff check` across all workspace members |
| `make backend-typecheck` | `pyright` across all workspace members |
| `make backend-test` | `pytest` across all workspace members |
| `make backend-check-all` | Format → lint → typecheck → test (sequential) |

---

## Key Constraints

1. **Single `.venv`** — All packages share one virtual environment. `uv sync` ensures every package's dependencies are installed there.
2. **Single `uv.lock`** — One lockfile for the entire workspace. Adding a dependency anywhere updates the lockfile.
3. **No circular dependencies** — Core has no deps on server/cli/tools. Server depends on core + tools. CLI depends on core + tools. Tools depends on core.
4. **Editable installs** — Intra-workspace packages are installed in editable mode, so edits to `myproject-core` are immediately visible to `myproject-server` without reinstalling.
5. **Hyphens in dirs, underscores in imports** — Always use `import myproject_core`, never `import myproject-core`.
