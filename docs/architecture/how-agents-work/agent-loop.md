# Agent Loop Architecture

This document describes the internal mechanics of the agent's execution loop — how the agent progresses through work by repeatedly calling the LLM, executing tools, and managing state until it reaches a conclusion or a termination condition.

---

## Steps vs Turns: Core Terminology

Understanding the distinction between **steps** and **turns** is essential to reasoning about the agent loop.

| Term | Definition | Scope |
|------|------------|-------|
| **Turn** | One LLM call — a single round-trip where messages are sent to the LLM provider and a response is received. A turn can produce text, tool calls, or both. | LLM provider level |
| **Step** | One call to `agent.step()` — the agent's unit of observable progress. A step consumes 1 to `max_turns` turns internally, ending when the LLM returns no tool calls (final response reached), or when a termination condition is hit. | Agent level |

**In practice:**

```
User calls agent.step("fix the bug")
    │
    ├─ Turn 1: LLM analyzes → tool_calls = [read_file(...)]
    ├─ Turn 2: LLM sees tool result → tool_calls = [edit_file(...)]
    ├─ Turn 3: LLM sees tool result → tool_calls = [read_file(...)]
    │
    └─ Step completes → returns final text to user

User calls agent.step("now write tests")
    │
    ├─ Turn 1: LLM writes tests → tool_calls = [write_file(...)]
    │
    └─ Step completes → returns final text to user
```

A **step** is what the external caller (e.g., the API endpoint) observes. A **turn** is what happens inside the loop. One step may require many turns, or just one.

---

## Loop Flow

Each `step()` call runs the following loop:

```
┌─────────────────────────────────────────────────────────────────┐
│                      agent.step(input)                          │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ 1. PREPARE TURN                                           │  │
│  │   • Append user message to memory.messages                │  │
│  │   • forget() — TTL decay, remove expired items             │  │
│  │   • remove_deleted_files() — purge files deleted on disk   │  │
│  │   • sync_entities() — refresh pinned DB entities          │  │
│  │   • sync_memory_tag_hints() / sync_user_profile()        │  │
│  └───────────────────────────┬───────────────────────────────┘  │
│                              ▼                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ 2. BUILD PAYLOAD                                          │  │
│  │   • Get messages from memory                              │  │
│  │   • Inject clipboard via _inject_clipboard()               │  │
│  │   • At max_turns - 3: inject "finalize" warning          │  │
│  └───────────────────────────┬───────────────────────────────┘  │
│                              ▼                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ 3. CALL LLM                                               │  │
│  │   • Stream content chunks → content_chunk_callbacks       │  │
│  │   • Stream reasoning chunks → reasoning_chunk_callbacks    │  │
│  │   • Receive: content, reasoning_content, tool_calls       │  │
│  └───────────────────────────┬───────────────────────────────┘  │
│                              ▼                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ 4. HANDLE RESPONSE                                        │  │
│  │                                                           │  │
│  │   If no tool_calls:                                       │  │
│  │     → Store assistant message in memory                   │  │
│  │     → Return content as final answer                      │  │
│  │                                                           │  │
│  │   If tool_calls exist:                                    │  │
│  │     → Loop detection check                                │  │
│  │     → Execute tools in parallel                           │  │
│  │     → Handle side-effects (clipboard, pinned entities)   │  │
│  │     → Store tool result messages in memory                │  │
│  │     → Loop back to step 1                                 │  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Step vs Turn: What Gets Stored

Only certain data is persisted to the agent's message history:

| Data | Stored in memory.messages? | Notes |
|------|--------------------------|-------|
| User messages | Yes | One per `step()` call |
| Assistant messages (with or without tool_calls) | Yes | One per turn that produced a response |
| Tool result messages | Yes | One per tool call |
| Clipboard content | **No** | Injected each turn as an ephemeral system message |

The clipboard is **never** stored in `memory.messages`. It is rebuilt each turn from current state and injected via `_inject_clipboard()`. This keeps the message history append-only, which is essential for LLM provider prompt caching.

---

## Termination Conditions

A step ends when any of these conditions is met:

### 1. LLM returns no tool calls
The most common happy path. The LLM produces a final text response, which is returned to the caller.

```
if not llm_response.tool_calls:
    return llm_response.content
```

### 2. Max turns reached
Each step has a configurable `max_turns` (default: 20). If the loop hits this limit before reaching a final response, the step terminates with a message indicating the limit was reached.

### 3. Loop detected
The agent detects when the LLM repeatedly makes the **exact same set of tool calls** with the **exact same arguments**. This catches weak models that get stuck in cycles.

```python
current_calls_signature = sorted([(tc.function_name, tc.arguments) for tc in llm_response.tool_calls])

if tool_call_history and current_calls_signature == tool_call_history[-1]:
    repeat_count = sum(1 for x in reversed(tool_call_history) if x == current_calls_signature) + 1
    if repeat_count >= max_repetitions:
        return f"Agent terminated: Detected a loop in tool calls ({llm_response.tool_calls[0].function_name})."
```

The `max_repetitions` default is 3 — if the same tool call signature appears 3 times consecutively, the step ends.

### 4. Max turns warning
At `max_turns - 3`, a warning message is injected into the LLM payload (not stored in history) to nudge the model toward wrapping up:
```
"WARNING: You are nearing the maximum step limit. Please finalize your work and provide a conclusion in the next 1-2 turns."
```

---

## Per-Turn Maintenance

Before each LLM call, several maintenance operations run:

### TTL Decay (`forget()`)
Every clipboard item has a `ttl` (time-to-live) that decrements by 1 each turn. When TTL reaches 0, the item is removed. This prevents stale data from accumulating.

For pinned entities, a **decay rule** applies: when TTL drops to 5 or below and resolution is "detail", it automatically downgrades to "summary" to reduce token usage.

```python
# Decay rule in reduce_ttl()
if entity.ttl <= 5 and entity.resolution == "detail":
    entity.resolution = "summary"
```

### File Synchronization (`remove_deleted_files()`)
Files added to the clipboard are checked against the filesystem each turn. If a file no longer exists on disk, it is removed from the clipboard.

### Database Sync (`sync_entities()`)
Pinned entities (tasks, projects, journals, memory events, memory topics) are **live-synced** from their respective databases each turn:

- For **productivity** entities (`user_db_url`): fetches latest task, project, journal records
- For **memory** entities (`memory_db_url`): fetches latest memory events and topics
- If a pinned entity was **deleted** from the database, it is automatically removed from the clipboard

This ensures the agent always acts on current data without storing snapshots in history.

---

## Clipboard Injection (`_inject_clipboard()`)

The clipboard is injected into the LLM payload as an **ephemeral system message** — it is never stored in `memory.messages`. This preserves prompt caching and keeps history lean.

Injection position follows three rules:

1. **Last message is a tool result** → clipboard content is **appended** to that tool result message
2. **Last message is a user message** → clipboard is **inserted just before** that user message
3. **No user or tool message found** → clipboard is **appended** to the end

```python
if history[-1]["role"] == "tool":
    # Append to last tool result
    tool_result_with_clipboard = history[-1].copy()
    tool_result_with_clipboard["content"] += f"\n\nClipboard context:\n{clipboard_text}"
    return history[:-1] + [tool_result_with_clipboard]

if last_user_index is not None:
    # Insert before last user message
    return history[:last_user_index] + [clipboard_msg] + history[last_user_index:]

# Fringe case
return history + [clipboard_msg]
```

---

## Tool Side-Effects

When a tool returns a `ToolResult`, the agent loop handles four potential side-effects:

| Field | Action |
|-------|--------|
| `tool_response` | Sent back to LLM as a tool result message (stored in `memory.messages`) |
| `files_to_add_to_clipboard` | File paths are read, content added to clipboard |
| `results_to_add_to_clipboard` | Text added to clipboard as tool call results |
| `entities_to_track` | Entities are pinned to clipboard (key = `{item_type}_{item_id}`), resetting TTL |

All four channels are processed in `_execute_tool_and_format()`. Tool execution itself is parallelized via `asyncio.gather()`, but the LLM sees them as sequential in the message history.

---

## Message Format

Messages stored in `memory.messages` follow the OpenAI tool-call format:

```python
# Assistant message (with tool calls)
{
    "role": "assistant",
    "content": "...",  # Optional text alongside tool calls
    "reasoning_content": "...",  # If model produces reasoning
    "tool_calls": [
        {
            "id": "call_abc123",
            "type": "function",
            "function": {"name": "read_file", "arguments": '{"path": "foo.txt"}'}
        }
    ]
}

# Tool result message
{
    "role": "tool",
    "tool_call_id": "call_abc123",
    "name": "read_file",
    "content": "File contents here..."
}
```

---

## Key Files

| File | Purpose |
|------|---------|
| `myproject-core/src/myproject_core/agent.py` | `Agent.step()` — the loop orchestrator |
| `myproject-core/src/myproject_core/agent_memory.py` | `AgentMemory` — message history + clipboard management |
| `myproject-core/src/myproject_core/schemas.py` | `AgentClipboard`, TTL/decay logic, rendering |
| `myproject-core/src/myproject_core/llm/__init__.py` | `get_llm_response()` — provider-agnostic LLM interface |
| `myproject-core/src/myproject_core/llm/_litellm.py` | LiteLLM implementation for OpenAI-compatible providers |
| `myproject-core/src/myproject_core/llm/_anthropic.py` | Anthropic SDK implementation |
| `myproject-tools/src/myproject_tools/schema.py` | `ToolResult`, `TrackedEntity` — tool output schema |

---

## Related Documentation

- [Agent Integration Architecture](./agent-integration-architecture.md) — how `step()` connects to the FastAPI server and frontend SSE stream
- [Agent Clipboard Architecture](./agent_clipboard_architecture.md) — clipboard content types, TTL semantics, live-sync, rendering
- [Tool Architecture](./tool_architecture.md) — how to build tools that leverage the multi-channel `ToolResult`
