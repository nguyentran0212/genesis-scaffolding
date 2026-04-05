# Productivity System

## Overview

The productivity system provides a personal task and information management layer — tasks, projects, calendar appointments, and journals — accessible to agents via tool calls. It is designed so agents can help users manage their work without requiring the agent to hold this state in context.

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Agent Loop                                      │
│   search_tasks() → pins task IDs to clipboard → render_to_markdown()   │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  Productivity Tools (9 tools)                        │
│  search_tasks, read_task, search_projects, read_project,              │
│  search_journals, read_journal, create_task, create_project,            │
│  create_journal, update_tasks, update_project, edit_journal             │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Productivity Service                              │
│   (myproject_core/productivity/service.py)                            │
│   CRUD operations, query builders, bulk updates                       │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  Productivity Models                                 │
│   (myproject_core/productivity/models.py)                            │
│   Task, Project, JournalEntry, ProjectTaskLink                       │
│   Stored in user's private SQLite database                            │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Data Model

### Task

The core unit of work. Tasks have two distinct time concepts:

**Floating dates** (calendar day only, no time):
- `assigned_date: date` — the day the user plans to work on this

**Absolute UTC timestamps** (time-aware):
- `hard_deadline: datetime` — a due date with time, e.g. "5pm Friday"
- `scheduled_start: datetime` — an appointment start time

The distinction matters: a task with `assigned_date = 2026-04-05` means "sometime on April 5th." A task with `hard_deadline = 2026-04-05T17:00:00Z` means "5pm UTC on April 5th — exactly."

```python
class Task(SQLModel, table=True):
    id: int | None
    title: str
    description: str | None

    # Floating — calendar day only
    assigned_date: date | None

    # Absolute UTC — includes timezone
    created_at: datetime
    completed_at: datetime | None
    hard_deadline: datetime | None       # "Boss deadline"
    scheduled_start: datetime | None     # "Appointment"
    duration_minutes: int | None

    status: Status  # backlog | todo | in_progress | completed | canceled

    # Many-to-many with Project
    projects: list[Project] = Relationship(back_populates="tasks", link_model=ProjectTaskLink)
```

### Project

A named container for related tasks and journals.

```python
class Project(SQLModel, table=True):
    id: int | None
    name: str
    description: str | None
    start_date: date | None
    deadline: date | None
    status: Status
```

### JournalEntry

A timestamped note or log. Types: `daily`, `weekly`, `monthly`, `yearly`, `project`, `general`.

```python
class JournalEntry(SQLModel, table=True):
    id: int | None
    entry_type: JournalType
    title: str | None
    content: str          # Markdown
    project_id: int | None
    reference_date: date  # The date this entry is "about"
```

### ProjectTaskLink

Many-to-many join table between Tasks and Projects.

---

## Time Handling Design

A key design decision: **two kinds of time, two storage strategies**.

| Kind | Examples | Storage | Meaning |
|---|---|---|---|
| **Floating** | `assigned_date`, project `start_date/deadline` | `date` (no timezone) | "The day on the user's calendar" |
| **Absolute** | `hard_deadline`, `scheduled_start` | `datetime(timezone=True)` | "An instant in UTC" |

**Why?** A task "due Friday" means different things in different timezones. By storing `hard_deadline` as an absolute UTC instant, the system can reason about ordering across users in different timezones. But storing it as just a date (`2026-04-05`) would discard the time-of-day.

The frontend converts user-local times ("9am Friday Adelaide") into UTC before sending to the API. The backend stores UTC. When rendering back to the user, the frontend converts to local time.

---

## Storage: Per-User Private Database

Productivity data lives in each user's **private SQLite database**, separate from the system database.

```
{internal_state_dir}/productivity/{user_id}.db
```

This is different from the **memory database** (`memory/user_memory.db`) which is also per-user. The productivity database and memory database are distinct — productivity stores work data, memory stores the agent's learned knowledge about the user.

Separation of concerns:
- **User DB** (`productivity/`) — tasks, projects, journals (work data)
- **Memory DB** (`memory/`) — EventLog, TopicalMemory (agent knowledge)

---

## Agent Tools

All 12 productivity tools are in `myproject-tools/src/myproject_tools/productivity_tools.py`. Each tool pins its results to the clipboard via `TrackedEntity`.

### Search Tools (Pin → Summary)

| Tool | Description |
|---|---|
| `search_tasks` | Filter by status, date range, project, free text. Returns task IDs pinned to clipboard as summaries. |
| `search_projects` | Filter by status, deadline, name. Returns project IDs pinned as summaries. |
| `search_journals` | Filter by type, date range, text. Returns journal IDs pinned as summaries. |

### Read Tools (Pin → Detail)

| Tool | Description |
|---|---|
| `read_task` | Fetch full task details + project links. Pinned as **detail** resolution. |
| `read_project` | Fetch full project details. Pinned as **detail** resolution. |
| `read_journal` | Fetch full journal markdown content. Pinned as **detail** resolution. |

### Write Tools (Pin → Detail After Create)

| Tool | Description |
|---|---|
| `create_task` | Creates task, pins the new task to clipboard in **detail** mode. |
| `create_project` | Creates project, pins to clipboard in **detail** mode. |
| `create_journal` | Creates journal with type-based reference date normalization. Pins to clipboard in **detail** mode. |
| `update_tasks` | Bulk update tasks. Pinned as **detail** (single) or **summary** (bulk). |
| `update_project` | Update project fields. |
| `edit_journal` | String-replace journal content. Uses exact-match safety: fails if the old string appears more than once. |

---

## Clipboard Integration

All productivity tools use `TrackedEntity` to signal the agent loop to pin results:

```python
entity = TrackedEntity(
    item_type="task",      # or "project", "journal"
    item_id=task_id,
    resolution="detail",  # or "summary"
    ttl=10,
)
return ToolResult(
    status="success",
    tool_response="Task pinned to clipboard.",
    entities_to_track=[entity],
)
```

The clipboard renders pinned entities differently per resolution:

| Resolution | Rendered fields |
|---|---|
| **summary** | ID, title/name, status, key dates |
| **detail** | summary + description, project links, full content |

The rendering happens in `AgentClipboard.render_to_markdown()`, which produces the "USER PRODUCTIVITY SYSTEM" section injected into the agent's context.

---

## Key Design Decisions

1. **Two clocks**: Floating vs absolute time is a deliberate distinction. It prevents timezone ambiguity for calendar-day semantics while preserving instant precision for deadlines and appointments.

2. **Productivity DB is not the memory DB**: Keeping productivity data in a separate database from the agent's memory database is intentional. Productivity is user-owned work data; memory is the agent's accumulated knowledge. They have different update patterns (CRUD vs append/revise).

3. **Clipboard as the view layer**: Productivity tools don't return full records in the tool response — they pin IDs and let the clipboard rendering handle formatting. This keeps tool responses compact while giving the agent full detail on demand.

4. **Exact-match journal editing**: `edit_journal` requires an exact string match for the old content and fails if the string appears multiple times. This is a deliberate safety guard — journals are long Markdown documents and blindly replacing the first occurrence would be dangerous.

5. **Completion timestamp auto-set**: When a task's status transitions to `completed`, `completed_at` is automatically set to `now(UTC)`. When transitioning out of `completed`, it is cleared. This prevents accidental completion dates being stale.

---

## Critical Files

| File | Purpose |
|---|---|
| `myproject-core/src/myproject_core/productivity/models.py` | `Task`, `Project`, `JournalEntry`, `ProjectTaskLink`, `Status`, `JournalType` |
| `myproject-core/src/myproject_core/productivity/service.py` | CRUD operations, query builders, bulk updates |
| `myproject-core/src/myproject_core/productivity/db.py` | `get_user_engine()`, `get_user_session()` — per-user SQLite lifecycle |
| `myproject-tools/src/myproject_tools/productivity_tools.py` | All 12 agent tools |
| `myproject-core/src/myproject_core/schemas.py` | `AgentClipboardPinnedEntity` with productivity `item_type` values |
| `myproject-core/src/myproject_core/prompts/fragments.py` | `FRAGMENT_PRODUCTIVITY_SYSTEM` — prompt guidance for productivity tools |
