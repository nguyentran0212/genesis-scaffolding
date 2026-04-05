# Prompt System Architecture

## Overview

System prompts are assembled from modular fragments at agent initialization time. Rather than a single monolithic prompt string, the system uses a factory function that selects and concatenates fragments based on the agent's configuration — which tools it has access to, whether it has a memory database, whether it has a working directory, and so on.

This approach enables:
- **Version-controlled prompt parts** — each fragment can be updated independently
- **Conditional inclusion** — subsystems are only mentioned when relevant (e.g., memory guidance only when memory tools are present)
- **Clear ownership** — prompt content is co-located with the subsystem it describes
- **Composable construction** — adding a new tool category requires only a new fragment and a condition in the builder

---

## Module Structure

```
myproject_core/src/myproject_core/prompts/
├── __init__.py      # Exports: build_system_prompt, BuildPromptConfig
├── fragments.py     # All prompt fragment strings
└── builder.py       # BuildPromptConfig and factory function
```

---

## `BuildPromptConfig`

Defined in `builder.py`, this model encapsulates everything the factory function needs to know:

```python
class BuildPromptConfig(BaseModel):
    system_prompt: str           # The agent-specific role block from the .md file
    allowed_tools: list[str]     # Tool names from agent_config.allowed_tools
    interactive: bool = False   # Whether the agent is in interactive mode
    has_memory_db: bool = False # True when memory_db_url is set
    has_user_db: bool = False   # True when user_db_url is set
    has_working_directory: bool = False
```

---

## `build_system_prompt()`

The factory function takes a `BuildPromptConfig` and returns a single string:

```python
def build_system_prompt(config: BuildPromptConfig) -> str:
    parts = []
    parts.append(BASE_INSTRUCTION)
    # ... conditional fragments appended based on config ...
    parts.append(config.system_prompt)  # agent role always last
    return "\n\n".join(parts)
```

The agent-specific `system_prompt` (from the `.md` agent definition file) is always appended last — it is the definitive role description and takes precedence over any generic guidance.

---

## Fragments

All fragments are string constants in `fragments.py`. Each fragment is self-contained and includes the Markdown heading that will appear in the final prompt.

### Fragment Reference

| Constant | Trigger | Purpose |
|----------|---------|---------|
| `BASE_INSTRUCTION` | Always | General instruction: pronoun conventions ("you" vs "me"), clipboard concept |
| `FRAGMENT_WORKING_DIRECTORY` | `has_working_directory` or file tools | How to use file tools, read/write/edit patterns |
| `FRAGMENT_MEMORY` | Memory tools present | Memory as the agent's own faculty; EventLog vs TopicalMemory; tag conventions; user profile guidance |
| `FRAGMENT_PRODUCTIVITY_SYSTEM` | `has_user_db` + productivity tools | Data model for tasks/projects/journals; tool names; principles |
| `FRAGMENT_WEB_TOOLS` | Web tools present | When to search vs fetch; citation expectations |
| `FRAGMENT_PDF_TOOLS` | PDF tool present | How to use `pdf_to_markdown` |

### Tag Conventions in `FRAGMENT_MEMORY`

Tags are framed as the agent's structured index of its own experience. Key conventions communicated to the agent:

- **Format**: hyphen-connected words (`user-preference`, `boss-interaction`)
- **Soft taxonomy**: `user-*` (user profile, preferences, life situation), `observation-*` (directly observed events), `fact-*` (recorded facts)
- **Quantity**: 1-3 tags per memory — quality over quantity
- **User profile**: subject=`"user-profile"`, tag=`["user-profile"]`, content as structured plain text

---

## Agent Initialization

In `agent.py`, the monolithic `SYSTEM_PROMPT_PREFIX` constants have been removed. Instead:

```python
from .prompts import build_system_prompt, BuildPromptConfig

prompt_config = BuildPromptConfig(
    system_prompt=agent_config.system_prompt,
    allowed_tools=agent_config.allowed_tools,
    interactive=agent_config.interactive,
    has_memory_db=memory_db_url is not None,
    has_user_db=user_db_url is not None,
    has_working_directory=working_directory is not None,
)
system_prompt = build_system_prompt(prompt_config)
```

The `system_prompt` string is then used to initialize `AgentMemory` as the first system message.

---

## Tool Category Detection

The builder uses frozen sets of tool names to detect which subsystems are active:

```python
_MEMORY_TOOL_NAMES = frozenset([
    "remember_this", "search_memories", "list_memories",
    "get_memory", "update_memory", "delete_memory", "rebuild_fts_index",
])

_PRODUCTIVITY_TOOL_NAMES = frozenset([
    "search_tasks", "read_task", "search_projects", ...
])

_FILE_TOOL_NAMES = frozenset([
    "read_file", "list_files", "write_file", ...
])
```

These sets make inclusion logic readable and maintainable. Adding a new tool to a category only requires adding the tool name to the set — no logic changes.

---

## Clipboard Rendering

The clipboard rendering in `AgentClipboard.render_to_markdown()` produces sections that are referenced by `FRAGMENT_MEMORY`:

| Clipboard Section | Rendered when |
|-------------------|---------------|
| `### MEMORY TAGS` | `memory_tag_hints` is non-empty |
| `### USER PROFILE` | Always — shows profile content or onboarding nudge |

`FRAGMENT_MEMORY` tells the agent to check these sections and use them for orientation and retrieval.

---

## Contrast: Old vs New

### Old (monolithic)

```python
if agent_config.allowed_tools:
    system_prompt = SYSTEM_PROMPT_PREFIX + agent_config.system_prompt
else:
    system_prompt = SYSTEM_PROMPT_PREFIX_NO_TOOL + agent_config.system_prompt
```

Problems with this approach:
- No way to conditionally include memory guidance without also including file guidance
- All agents with tools got the same prompt regardless of which tools they actually had
- Prompt content was mixed with agent initialization logic
- Impossible to version-control individual prompt sections independently

### New (fragment-based)

```python
prompt_config = BuildPromptConfig(
    system_prompt=agent_config.system_prompt,
    allowed_tools=agent_config.allowed_tools,
    has_memory_db=memory_db_url is not None,
    ...
)
system_prompt = build_system_prompt(prompt_config)
```

Benefits:
- Only subsystems the agent actually has access to are mentioned in the prompt
- Prompt content is organized by topic in `fragments.py`
- The builder is a pure function — testable in isolation
- Adding a new tool category requires adding a fragment and a condition, nothing else

---

## Key Design Decisions

1. **Agent role last**: The `system_prompt` from the `.md` file is always appended last so the agent definition takes precedence over generic guidance
2. **Non-interactive**: The builder is intentionally stateless — it produces a string and knows nothing about the agent loop
3. **Frozen sets for tool categories**: Tool detection uses `frozenset.isdisjoint()` which is fast and readable
4. **Soft taxonomy for tags**: The `user-*` / `observation-*` / `fact-*` taxonomy is suggested, not enforced — the agent has agency to create its own categories
5. **No TTL on rendered snapshots**: `memory_tag_hints` and `user_profile_content` in the clipboard are refreshed every turn and are not subject to TTL decay

---

## Critical Files

| File | Purpose |
|------|---------|
| `myproject-core/src/myproject_core/prompts/__init__.py` | Module exports |
| `myproject-core/src/myproject_core/prompts/builder.py` | `BuildPromptConfig`, tool category sets, `build_system_prompt()` |
| `myproject-core/src/myproject_core/prompts/fragments.py` | All prompt fragment strings |
| `myproject-core/src/myproject_core/agent.py` | Removes `SYSTEM_PROMPT_PREFIX`; uses `build_system_prompt()` |
| `myproject-core/src/myproject_core/schemas.py` | `AgentClipboard.render_to_markdown()` produces clipboard sections referenced by fragments |
