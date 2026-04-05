# Platform Layer

## Overview

The platform layer spans two packages: **`myproject-core`** (shared Python logic) and **`myproject-server`** (FastAPI REST API). Understanding what lives where — and how they interact — is key to extending either side.

```
┌────────────────────────────────────────────────────────────────────────────┐
│                          myproject-server (FastAPI)                          │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ Routers: auth │ users │ files │ workflows │ jobs │ schedules │ chat │  │
│  │              agents │ llm_config │ productivity │ memory               │  │
│  ├──────────────────────────────────────────────────────────────────────┤  │
│  │ ChatManager ── ActiveRun ── SSE streaming                            │  │
│  │ SchedulerManager (APScheduler)                                        │  │
│  │ Dependencies: per-user Config, Session, Registry injection           │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
├────────────────────────────────────────────────────────────────────────────┤
│                          myproject-core (Shared)                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ AgentRegistry, WorkflowRegistry, WorkspaceManager, WorkflowEngine     │  │
│  │ AgentMemory, clipboard, prompts, LLM abstraction                      │  │
│  │ configs.py (three-layer loading: env → YAML → user isolation)         │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────────┘
```

### What Lives in `myproject-core`

| Module | Purpose |
|---|---|
| `agent_registry.py` | Loads agent definitions from markdown files; manages `AgentBlueprint` and `Agent` instances |
| `workflow_registry.py` | Loads workflow manifests (YAML) from search paths |
| `workflow_engine.py` | Executes workflows: step sequencing, callbacks, blackboard |
| `workspace.py` | Sandboxed filesystem workspace per user |
| `agent_memory.py` | In-memory message history + clipboard state for an agent session |
| `clipboard.py` | TTL-based token budget management via LRU + decay |
| `llm/` | `get_llm_response()` entry point, LiteLLM + Anthropic SDK paths |
| `prompts/` | Fragment-based system prompt assembly |
| `memory/` | EventLog + TopicalMemory models + service layer (FTS5) |
| `configs.py` | `get_config()` with three-layer loading and user isolation |

### What Lives in `myproject-server`

| Module | Purpose |
|---|---|
| `main.py` | FastAPI app, lifespan (init → sync → start), 11 router registrations |
| `dependencies.py` | Per-request dependency injection: current user, user config, user DB session, registries |
| `database.py` | System DB engine (SQLite), `init_db()`, `seed_admin_user()`, `get_session()` |
| `chat_manager.py` | Global `ChatManager` singleton; SSE broadcast via `ActiveRun` queues |
| `scheduler.py` | `SchedulerManager`: APScheduler wrapper, per-user just-in-time context resolution |
| `routers/chat.py` | Chat sessions, SSE streaming endpoint, message persistence |
| `routers/agents.py` | CRUD for user-defined agent blueprints |
| `routers/workflows.py` | Workflow manifest listing/detail |
| `routers/schedules.py` | Cron schedule CRUD; sync with APScheduler |
| `routers/jobs.py` | Workflow job submission, SSE stream, output listing |
| `routers/productivity.py` | Tasks, Projects, Journals, Calendar CRUD (per-user DB) |
| `routers/memory.py` | EventLog + TopicalMemory CRUD (per-user DB) |
| `routers/files.py` | File upload/download within user sandbox |
| `routers/llm_config.py` | Per-user LLM provider/model configuration |
| `routers/auth.py` | Login, refresh token |
| `auth/security.py` | JWT creation/verification, Argon2id password hashing |
| `utils/config_persistence.py` | Write to user's `config.yaml` |

---

## FastAPI App and Lifespan

**File:** `myproject-server/src/myproject_server/main.py`

The app uses FastAPI's lifespan context manager pattern:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Initialize system database (create tables, seed admin)
    init_db()
    # 2. Sync all enabled cron schedules from DB into APScheduler
    await app.state.scheduler.sync_schedules()
    # 3. Start the scheduler
    app.state.scheduler.start()
    yield
    # 4. Shutdown
    app.state.scheduler.stop()
```

The `app.state` object holds two things set during startup:
- `chat_manager: ChatManager` — global singleton for SSE broadcast
- `scheduler: SchedulerManager` — APScheduler wrapper

---

## Dependency Injection

**File:** `myproject-server/src/myproject_server/dependencies.py`

All user-scoped dependencies resolve from the incoming JWT token. The `get_current_active_user()` dependency decodes the Bearer token and looks up the `User` record in the system DB.

### Key Dependencies

| Function | Returns | Notes |
|---|---|---|
| `get_current_active_user()` | `User` | JWT decode → DB lookup |
| `get_user_workdir()` | `Path` | `{server_users_directory}/{user.id}/` |
| `get_user_config()` | `Config` | Calls `get_config(user_workdir=...)` for three-layer loading |
| `get_user_inbox_path()` | `Path` | `working_directory` from user's Config |
| `get_session()` | `Session` | System DB session |
| `get_user_session()` | `Session` | Per-user **productivity** SQLite DB |
| `get_memory_session()` | `Session` | Per-user **memory** SQLite DB |
| `get_agent_registry()` | `AgentRegistry` | Scoped to user's config |
| `get_workflow_registry()` | `WorkflowRegistry` | Scoped to user's config |
| `get_workspace_manager()` | `WorkspaceManager` | Scoped to user's config |
| `get_workflow_engine()` | `WorkflowEngine` | Scoped to user's config |
| `get_scheduler_manager()` | `SchedulerManager` | Global singleton from `app.state` |

Type aliases (e.g., `UserConfigDep`, `ProdSessionDep`) are defined for cleaner router signatures.

---

## Three-Database Architecture

The server manages three separate SQLite databases:

```
server_root_directory/
├── myproject.db                        ← System DB (shared)
│   ├── User accounts
│   ├── WorkflowSchedule
│   └── ChatSession, ChatMessage
└── users/{user_id}/
    ├── config.yaml                      ← Per-user config override
    ├── productivity.db                  ← Per-user productivity (tasks, projects, journals)
    └── memory.db                        ← Per-user agent memory (EventLog, TopicalMemory)
```

### System DB (`db`)

Module-level singleton at `myproject_server.database`:

```python
engine = create_engine(f"sqlite:///{server_root_directory}/myproject.db")
```

Tables: `User`, `WorkflowSchedule`, `ChatSession`, `ChatMessage`, `WorkflowJob`, `FileRecord`

### User DBs

Resolved per-request via `get_user_session()` or `get_memory_session()`. These open the user's private SQLite file inside their `{server_users_directory}/{user_id}/` directory.

---

## Configuration System

**File:** `myproject-core/src/myproject_core/configs.py`

The configuration loads in three layers (later layers override earlier ones):

### Layer 1: Environment Variables
All variables are prefixed with `myproject__` and nested with `__`:

```bash
myproject__server__host=0.0.0.0
myproject__server__port=8000
```

### Layer 2: YAML Override File
Passed as `override_yaml` to `get_config()`. The server passes the **server-level** `config.yaml` (at `server_root_directory/config.yaml`).

### Layer 3: User Isolation
For user-specific overrides, `get_user_config()` is called with `user_workdir`, which points to the user's directory. This is `get_config(user_workdir=...)` — internally it anchors the system DB path to the server root but sets the user's `working_directory` and `internal_state_dir` to their own space.

### User Isolation Logic

```python
if user_workdir:
    _override = {
        "path": {
            "internal_state_dir": user_workdir / "internal_state",
            "working_directory": user_workdir / "working",
        }
    }
    # Deep-merges user overrides on top of server-level config
    merged = deep_merge(base_config, _override)
```

Key derived paths in `Config.path`:
- `agent_search_paths` — list of directories to scan for agent markdown files
- `workflow_search_paths` — list of directories to scan for workflow YAML
- `workspace_directory` — sandbox root for file operations
- `inbox_directory` — `working_directory` (user's personal inbox)
- `internal_state_dir` — where productivity.db and memory.db live

---

## SSE Streaming: ChatManager and ActiveRun

**File:** `myproject-server/src/myproject_server/chat_manager.py`

### `ChatManager` (Global Singleton)

Holds `active_runs: dict[session_id, ActiveRun]`. Manages SSE client subscriptions per session.

### `ActiveRun` (Per-Session)

Created when a chat session starts processing. Holds:
- `messages: list[str]` — accumulated interim messages for catchup
- `client_queues: list[asyncio.Queue]` — one queue per SSE client
- `lock: asyncio.Lock` — prevents concurrent agent steps

### SSE Events

| Event | Triggered When |
|---|---|
| `reasoning` | Extended thinking/reasoning chunk arrives from LLM |
| `content` | Text content chunk arrives from LLM |
| `tool_start` | Agent begins executing a tool |
| `tool_result` | Tool finishes, result text available |
| `catchup` | Sent on new SSE connection — contains all messages produced in current step |

### Streaming Endpoint

`GET /chats/{session_id}/stream` — SSE endpoint:
1. Sends `catchup` event with all interim messages
2. Loops reading from `client_queue` (populated by `ActiveRun` callbacks)
3. On disconnect or terminal signal, removes client from queue

### Post-Run Persistence

After the agent step completes in a background task:
1. New messages are extracted from `agent.memory.messages` (only new ones since start)
2. Written to `ChatMessage` table via a fresh DB session
3. `ChatSession.clipboard_state` updated with the agent's clipboard
4. `is_running` flag cleared

---

## Scheduler Manager

**File:** `myproject-server/src/myproject_server/scheduler.py`

`SchedulerManager` wraps `APScheduler.AsyncIOScheduler`. It runs in the background across the server's lifetime.

### Initial Sync

On server start (`lifespan` → `sync_schedules()`):
1. Loads all `WorkflowSchedule` records where `enabled=True`
2. Calls `upsert_schedule()` for each — adds to APScheduler with a cron trigger

### Per-Schedule Execution

When a cron trigger fires:

```python
async def _execute_scheduled_task(self, schedule_id: int, user_id: int):
    # 1. Load Schedule + User from DB
    # 2. Resolve user context JUST-IN-TIME:
    user_workdir = server_settings.path.server_users_directory / str(user.id)
    user_config = get_config(user_workdir=user_workdir, override_yaml=user_workdir / "config.yaml")
    user_registry = WorkflowRegistry(user_config)
    user_agent_registry = AgentRegistry(user_config)
    user_engine = WorkflowEngine(WorkspaceManager(user_config), user_agent_registry)
    # 3. Create job record, run via run_workflow_job(...)
```

This just-in-time resolution means schedules always use the user's **current** config and registry state — even if they updated their agent definitions or workflows since the server started.

### Upsert / Remove

- `upsert_schedule()` — adds or replaces an APScheduler job with `CronTrigger.from_crontab()`
- `remove_schedule()` — removes job from APScheduler (no-op if already removed)

---

## REST API Routers

All routers are registered in `main.py` via `app.include_router(...)` with authentication dependencies on every endpoint.

### Auth Router (`/auth`)

| Method | Path | Description |
|---|---|---|
| POST | `/auth/login` | OAuth2 password flow → returns JWT access + refresh token |
| POST | `/auth/refresh` | Exchange refresh token for new access token |

### Users Router (`/users`)

| Method | Path | Description |
|---|---|---|
| GET | `/users/me` | Current user profile |
| PATCH | `/users/me` | Update display name or password |

### Agents Router (`/agents`)

| Method | Path | Description |
|---|---|---|
| GET | `/agents/` | List all available agent blueprints |
| POST | `/agents/` | Create a new agent (saves markdown file to user's directory) |
| GET | `/agents/{agent_id}` | Get full agent metadata |
| PATCH | `/agents/{agent_id}` | Edit agent definition |
| DELETE | `/agents/{agent_id}` | Delete agent (fails if `read_only`) |

### Chat Router (`/chats`)

| Method | Path | Description |
|---|---|---|
| GET | `/chats/` | List all chat sessions |
| POST | `/chats/` | Create session (initializes agent + system prompts) |
| GET | `/chats/{session_id}` | Get session + full message history |
| POST | `/chats/{session_id}/message` | Send message, run agent in background → 202 |
| GET | `/chats/{session_id}/stream` | SSE stream for live updates |

### Workflows Router (`/workflows`)

| Method | Path | Description |
|---|---|---|
| GET | `/workflows/` | List all available workflow manifests |
| GET | `/workflows/{workflow_id}` | Get specific workflow manifest |

### Schedules Router (`/schedules`)

| Method | Path | Description |
|---|---|---|
| GET | `/schedules/` | List all schedules for current user |
| POST | `/schedules/` | Create schedule (upserts into APScheduler) |
| GET | `/schedules/{schedule_id}` | Get schedule detail |
| PATCH | `/schedules/{schedule_id}` | Update (syncs with APScheduler) |
| DELETE | `/schedules/{schedule_id}` | Delete from DB + APScheduler |

### Jobs Router (`/jobs`)

| Method | Path | Description |
|---|---|---|
| POST | `/jobs/` | Submit a workflow job (runs in background) |
| GET | `/jobs/` | List jobs for current user |
| GET | `/jobs/{job_id}` | Get job detail + status |
| GET | `/jobs/{job_id}/stream` | SSE stream for job step events |
| GET | `/jobs/{job_id}/output` | List files in job's output directory |
| GET | `/jobs/{job_id}/output/{path}` | Download specific output file |

### Productivity Router (`/productivity`)

Full CRUD for Tasks, Projects, Journals, Calendar entries, and Project-Task links. Uses `get_user_session()` for per-user database isolation.

### Memory Router (`/memory`)

CRUD for EventLog and TopicalMemory. FTS5 full-text search via `/memory/search`. Uses `get_memory_session()`.

### Files Router (`/files`)

| Method | Path | Description |
|---|---|---|
| POST | `/files/upload` | Upload file to user's sandbox |
| GET | `/files/` | List files (optionally filtered by folder) |
| GET | `/files/{file_id}/download` | Download file |
| DELETE | `/files/{file_id}` | Delete file |
| GET | `/files/folders` | List immediate subfolders |

Path traversal is blocked: all file operations are sandboxed under `user_inbox_path`.

### LLM Config Router (`/configs/llm`)

| Method | Path | Description |
|---|---|---|
| GET | `/configs/llm/` | Get current providers + models + default |
| POST | `/configs/llm/providers/{nickname}` | Add/update provider in user's `config.yaml` |
| DELETE | `/configs/llm/providers/{nickname}` | Remove provider |
| POST | `/configs/llm/models/{nickname}` | Add/update model in user's `config.yaml` |
| DELETE | `/configs/llm/models/{nickname}` | Remove model |
| PATCH | `/configs/llm/settings` | Update default model |

Writes go directly to the user's `config.yaml` via `update_user_yaml_config()` / `update_user_top_level_config()`.

---

## Auth Flow

1. User submits username + password to `POST /auth/login`
2. Server verifies against `User.hashed_password` (Argon2id via `pwdlib`)
3. Returns `Token` with `access_token` (15 min JWT), `refresh_token` (7 day JWT), and `expires_in`
4. Client includes `Authorization: Bearer <token>` on all subsequent requests
5. `get_current_active_user()` dependency decodes JWT, looks up user in system DB
6. `POST /auth/refresh` exchanges a valid refresh token for a new access token

JWT payload: `{"exp": ..., "sub": "<username>", "type": "refresh?"}`

---

## Server-Side Config vs User Config

| Aspect | Server Config | User Config |
|---|---|---|
| Loading | `get_config()` | `get_config(user_workdir=...)` |
| YAML source | `server_root_directory/config.yaml` | `users/{user_id}/config.yaml` |
| System DB path | Always `server_root_directory/myproject.db` | Anchored to server root |
| Working directory | Server's configured default | Per-user `users/{user_id}/working` |
| LLM providers | None by default | User-configured |
| Agent paths | Server-level defaults | Per-user overrides |

The user config's `deep_merge` with `{"path": {"internal_state_dir": ..., "working_directory": ...}}` ensures the user's productivity and memory databases live inside their own directory, achieving complete data isolation.

---

## Key Design Decisions

1. **Three separate databases** — System DB is shared; user productivity and memory DBs are private. This means the server never mixes user data at the storage layer.
2. **Just-in-time user context for scheduled jobs** — The scheduler resolves user config at execution time, not startup time. Agent/workflow updates take effect immediately without server restart.
3. **JWT + per-user DB session** — Auth is stateless (JWT), but data access is stateful (per-user SQLite). The JWT identifies the user; the dependency injection opens their specific DB file.
4. **SSE over WebSocket** — Chosen for simplicity. The `ChatManager` broadcasts to in-memory queues; no external message broker needed.
5. **Config writes go to YAML, not DB** — LLM provider/model configuration is stored in `config.yaml` (version-controlled, human-editable) rather than a database table.
6. **Sandboxed file operations** — All file paths are resolved relative to `user_inbox_path`; path traversal is blocked via `startswith()` checks.
