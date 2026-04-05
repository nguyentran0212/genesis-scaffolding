# Agent Registry

## Overview

**File:** `myproject-core/src/myproject_core/agent_registry.py`

The `AgentRegistry` loads **agent definitions** from markdown files (with YAML frontmatter) and acts as a factory for spawning agent instances. It is **config-scoped**: the same class works for both the server (per-user registry with user-specific search paths) and the CLI (shared registry with default search paths).

```
AgentRegistry
├── blueprints: dict[str, AgentConfig]   ← loaded metadata (not instances)
├── agent_search_paths: list[Path]        ← from Config.path.agent_search_paths
└── settings: Config                      ← used for LLM config resolution
```

---

## Loading Agents from Markdown Files

`AgentRegistry.load_all()` scans every directory in `agent_search_paths` for `*.md` files:

```python
for md_file in agent_dir.glob("*.md"):
    agent_manifest = frontmatter.load(str(md_file))
    raw_data = agent_manifest.metadata
    raw_data["system_prompt"] = agent_manifest.content.strip()
```

**Frontmatter schema** (with example from `assistant_agent.md`):

```yaml
---
name: "Max"
description: "Max is a helpful and professional assistant"
interactive: true
read_only: true
allowed_tools:
  - search_web
  - read_file
  - search_tasks
  - ...
---

System prompt goes here as the markdown body.
```

### Frontmatter Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | `str` | Yes | Display name of the agent |
| `description` | `str` | Yes | Human-readable description shown in the frontend |
| `interactive` | `bool` | No | If `true`, the agent can be used in chat sessions (default: `false`) |
| `read_only` | `bool` | No | If `true`, users cannot edit or delete the agent via API (default: `false`) |
| `allowed_tools` | `list[str]` | No | Whitelist of tool names the agent may use; empty = all tools |
| `allowed_agents` | `list[str]` | No | Whitelist of other agent IDs this agent may delegate to |
| `model_name` | `str` | No | LLM model nickname from the user's config (e.g., `"claude-sonnet"`). If omitted, uses the user's default model |

The **markdown body** (after the `---` closing line) becomes the agent's `system_prompt`.

### LLM Config Resolution

When `load_all()` encounters a `model_name` in the frontmatter, it resolves it against the registry's `Config`:

```python
llm_model_name = raw_data.get("model_name", "")
[llm_config, provider_config] = self._get_llm_model_config(llm_model_name)
```

```python
def _get_llm_model_config(self, model_name: str | None = None) -> tuple[LLMModelConfig, LLMProvider]:
    if not model_name or model_name not in self.settings.models.keys():
        return self.settings.default_llm_config   # falls back to user's default
    llm_model_config = self.settings.models[model_name]
    provider_config = self.settings.providers[llm_model_config.provider]
    return (llm_model_config, provider_config)
```

This means agents are bound to **configured models**, not hardcoded model strings — users select providers and models in the frontend and the agent picks them up automatically.

---

## Blueprint vs Instance

The registry stores **`AgentConfig` blueprints**, not `Agent` instances. Instances are created on-demand via `create_agent()`:

```python
def create_agent(
    self,
    name: str,                        # blueprint key (markdown filename stem)
    working_directory: Path | None = None,
    memory: AgentMemory | None = None,
    **overrides,                       # runtime overrides to the blueprint
) -> Agent:
    blueprint = self.blueprints.get(name)
    instance_config = blueprint.model_copy(deep=True, update=overrides)
    return Agent(
        agent_config=instance_config,
        working_directory=working_directory,
        memory=memory,
        timezone=self.settings.timezone,
        user_db_url=self.settings.user_db.connection_string,
        memory_db_url=self.settings.memory_db.connection_string,
    )
```

---

## Persistence: Adding, Editing, Deleting Agents

The registry is backed by markdown files on disk. Only agents in the **last** search path (the user-specific directory) can be created, edited, or deleted.

### Adding an Agent

```python
agent_id = agent_reg.add_agent({
    "name": "Research Assistant",
    "description": "Helps search and summarize papers",
    "interactive": True,
    "allowed_tools": ["search_arxiv_paper", "get_arxiv_paper_detail"],
    "system_prompt": "You are a research assistant...",
})
# Saves to: {user_workdir}/agents/{slugified_name}.md
# Returns the slugified agent_id
```

The `add_agent()` method:
1. Slugifies the name (e.g., `"Research Assistant"` → `"research_assistant"`)
2. Handles collisions by appending a UUID suffix
3. Writes a new markdown file with frontmatter + body
4. Calls `load_all()` to refresh the in-memory registry

### Editing an Agent

```python
agent_reg.edit_agent("research_assistant", {
    "description": "Updated description",
    "system_prompt": "New system prompt...",
})
```

- Loads the existing file, merges updated metadata, rewrites atomically (write to `.tmp` → rename)
- Raises `ValueError` if the agent is `read_only`

### Deleting an Agent

```python
agent_reg.delete_agent("research_assistant")
```

- Removes the markdown file from disk
- Raises `ValueError` if the agent is `read_only`
- Calls `load_all()` to refresh

---

## Server-Side Agent Management

**File:** `myproject-server/src/myproject_server/routers/agents.py`

The FastAPI agents router wraps the registry for HTTP access:

| Method | Path | Description |
|---|---|---|
| GET | `/agents/` | List all available agent blueprints |
| POST | `/agents/` | Create a new agent (saves markdown file to user's agent dir) |
| GET | `/agents/{agent_id}` | Get full agent metadata |
| PATCH | `/agents/{agent_id}` | Edit agent definition |
| DELETE | `/agents/{agent_id}` | Delete agent (fails if `read_only`) |

The server uses `get_agent_registry()` dependency which resolves the registry using the **user's config** — meaning each user's agents directory is isolated.

---

## `AgentConfig` Schema

**File:** `myproject-core/src/myproject_core/schemas.py`

```python
class AgentConfig(BaseModel):
    name: str
    model_name: str | None = None           # resolved to llm_config + provider_config at load time
    llm_config: LLMModelConfig | None = None
    provider_config: LLMProvider | None = None
    interactive: bool = False
    system_prompt: str = "You are a helpful AI agent."
    description: str = "An AI Assistant Agent."
    allowed_tools: list[str] = []
    allowed_agents: list[str] = []
    read_only: bool = False
```

`llm_config` and `provider_config` are injected by the registry at load time based on `model_name`.

---

## Key Design Decisions

1. **Frontmatter + markdown body** — Agent definitions are human-readable files that can be version-controlled. The frontmatter carries metadata; the body is the system prompt.
2. **Config-scoped resolution** — Agents don't hardcode model names. They reference a nickname in `model_name` that the registry resolves against the current user's configured models and providers.
3. **Read-only agents** — Built-in agents (like "Max") can be marked `read_only` to prevent users from modifying or deleting them through the API.
4. **Atomic file writes** — `edit_agent()` writes to a `.tmp` file then renames, avoiding partial writes on crash.
5. **Last search path wins for writes** — Only the last entry in `agent_search_paths` (the user-specific directory) is used for creates, edits, and deletes. This preserves built-in agents in earlier directories.
