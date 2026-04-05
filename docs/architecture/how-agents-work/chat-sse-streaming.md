# Chat SSE Streaming

## Overview

This document describes the end-to-end data flow and control logic for chat interactions in this application. It covers how a user's message travels from the React frontend through the FastAPI server, into the agent core for processing, and back through Server-Sent Events (SSE) for real-time display — including the callback system that bridges the agent's internal execution to external consumers.

**Scope:** Logic, control flow, and data flow. Does not cover the agent's internal reasoning loop.

---

## Component Map

| Component | Path |
|-----------|------|
| Agent class | `myproject-core/src/myproject_core/agent.py` |
| AgentMemory class | `myproject-core/src/myproject_core/agent_memory.py` |
| AgentRegistry class | `myproject-core/src/myproject_core/agent_registry.py` |
| Callback type definitions | `myproject-core/src/myproject_core/schemas.py` |
| ChatManager / ActiveRun | `myproject-server/src/myproject_server/chat_manager.py` |
| Chat router (endpoints) | `myproject-server/src/myproject_server/routers/chat.py` |
| Frontend ChatProvider | `myproject-frontend/components/chat/chat-context.tsx` |
| Frontend MessageBubble | `myproject-frontend/components/chat/message-bubble.tsx` |
| Chat types | `myproject-frontend/types/chat.ts` |

---

## 1. Callback System

The agent communicates with external consumers through four callback types, defined in `myproject-core/src/myproject_core/schemas.py`:

```python
StreamCallback = Callable[[str], Awaitable[None]]  # For content and reasoning chunks

ToolCallback = Callable[[str, dict[str, Any]], Awaitable[None]]
# For tool_start and tool_result — receives (tool_name, tool_args_or_result)
```

These callbacks are passed into the `Agent` constructor and invoked during `step()` execution:

**File:** `myproject-core/src/myproject_core/agent.py` (lines 366-385)

```python
# Tool start — called before tool execution begins
if tool_start_callback:
    await asyncio.gather(*[cb(tc.function_name, args) for cb in tool_start_callback])

# Tool result — called after tool execution completes
if tool_result_callback:
    await asyncio.gather(*[
        cb(res_msg["name"], {"result": res_msg["content"]}) for cb in tool_result_callback
    ])
```

---

## 2. FastAPI: ChatManager and ActiveRun

**File:** `myproject-server/src/myproject_server/chat_manager.py`

`ChatManager` is a app-level singleton that holds `ActiveRun` instances per session. Each `ActiveRun` manages the state of an in-progress agent execution and maintains a list of `asyncio.Queue` instances — one per connected SSE client.

### ActiveRun structure

```python
class ActiveRun:
    def __init__(self, session_id: int, user_input: str):
        self.session_id = session_id
        self.messages: list[dict[str, Any]] = [{"role": "user", "content": user_input}]
        self.clients: list[asyncio.Queue] = []  # SSE subscriber queues

    async def handle_content(self, chunk: str):
        """Appends text chunk to the last assistant message, broadcasts to all clients"""
        # ... (broadcasts "content" SSE event)

    async def handle_reasoning(self, chunk: str):
        """Appends reasoning chunk, broadcasts to all clients"""

    async def handle_tool_start(self, name: str, args: dict):
        """Adds a tool_calls entry with status='running', broadcasts 'tool_start'"""

    async def handle_tool_result(self, name: str, args: dict):
        """Marks tool as completed, replaces index with full tool message, broadcasts 'tool_result'"""
```

### Broadcasting

Each `handle_*` method internally calls `_broadcast(event, payload, index)` which puts the payload into every connected client's queue:

```python
async def _broadcast(self, event: str, payload: dict, index: int):
    for queue in self.clients:
        await queue.put({"event": event, "data": payload, "index": index})
```

---

## 3. FastAPI: Chat Router Endpoints

**File:** `myproject-server/src/myproject_server/routers/chat.py`

### POST `/chats/{session_id}/message` (lines 114-218)

This endpoint initiates an agent run. It:

1. Validates the session and checks `is_running` concurrency lock
2. Reconstructs `AgentMemory` from database messages + clipboard state
3. Gets or creates an `ActiveRun` from `ChatManager`
4. **Binds the ActiveRun's handlers directly as callbacks to `agent.step()`:**
   ```python
   await agent.step(
       input=user_input,
       stream=True,
       content_chunk_callbacks=[active_run.handle_content],
       reasoning_chunk_callbacks=[active_run.handle_reasoning],
       tool_start_callback=[active_run.handle_tool_start],
       tool_result_callback=[active_run.handle_tool_result],
   )
   ```
5. Dispatches `run_agent_task()` to a background task
6. Returns `202 Accepted` immediately

The background task persists new messages to the database and clears `is_running` after the agent completes.

### GET `/chats/{session_id}/stream` (lines 221-260)

This endpoint streams SSE events to the frontend:

1. On connect, sends a **catchup** event containing all interim messages accumulated so far:
   ```
   event: catchup
   data: {"interim_messages": [...]}
   ```
2. Then loops, waiting on the client's queue and yielding SSE events:
   ```
   event: content
   data: {"data": "...", "index": 1}

   event: reasoning
   data: {"data": "...", "index": 1}

   event: tool_start
   data: {"data": {"name": "Read", "args": {...}}, "index": 1}

   event: tool_result
   data: {"data": {"role": "tool", "name": "Read", "content": "..."}, "index": 2}
   ```
3. Cleans up the client queue on disconnect.

---

## 4. Frontend: ChatProvider and SSE Connection

**File:** `myproject-frontend/components/chat/chat-context.tsx`

The `ChatProvider` establishes an SSE connection whenever `isRunning` is true (lines 65-135):

```typescript
const eventSource = new EventSource(`/api/chats/${session.id}/stream`);

eventSource.addEventListener('catchup', (e) => {
    // Initialize ephemeral message buffer with all interim messages
    activeRunRef.current = JSON.parse(e.data).interim_messages;
});

eventSource.addEventListener('content', (e) => {
    const { data, index } = JSON.parse(e.data);
    activeRunRef.current[index].content += data;
});

eventSource.addEventListener('reasoning', (e) => {
    const { data, index } = JSON.parse(e.data);
    activeRunRef.current[index].reasoning_content =
        (activeRunRef.current[index].reasoning_content || "") + data;
});

eventSource.addEventListener('tool_start', (e) => {
    const { data, index } = JSON.parse(e.data);
    activeRunRef.current[index].tool_calls!.push({ ...data, status: 'running' });
});

eventSource.addEventListener('tool_result', (e) => {
    const { data, index } = JSON.parse(e.data);
    // Update tool status to completed, replace index with full tool message
    activeRunRef.current[index] = data;
});
```

### 10fps Display Throttle

Direct SSE updates go into `activeRunRef.current` without triggering React re-renders. A 10fps `setInterval` (lines 35-50) reads the ref and updates `displayActiveMessages` state:

```typescript
const interval = setInterval(() => {
    setDisplayActiveMessages(activeRunRef.current.filter(Boolean).map(msg => ({
        ...msg,
        tool_calls: Array.isArray(msg.tool_calls) ? [...msg.tool_calls] : undefined
    })));
}, 100);
```

---

## 5. Complete Data Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│ 1. USER SENDS MESSAGE                                                   │
│    Frontend: sendMessage() → POST /chats/{id}/message                   │
└────────────────────────────┬──────────────────────────────────────────┘
                             │
┌────────────────────────────▼──────────────────────────────────────────┐
│ 2. FASTAPI ENDPOINT (chat.py → send_message)                          │
│    • Validate session, check is_running lock                           │
│    • Reconstruct AgentMemory from DB                                   │
│    • Create Agent via AgentRegistry                                    │
│    • Get ChatManager ActiveRun                                         │
│    • Bind ActiveRun callbacks to agent.step()                          │
│    • Dispatch agent execution to background task                       │
│    • Return 202 Accepted                                              │
└────────────────────────────┬──────────────────────────────────────────┘
                             │
┌────────────────────────────▼──────────────────────────────────────────┐
│ 3. AGENT EXECUTION (agent.py → step method)                            │
│    Loop (up to max_turns):                                             │
│      ├─ Sync pinned entities from DB                                  │
│      ├─ Inject clipboard into history                                  │
│      ├─ Call LLM via get_llm_response() with streaming                 │
│      │     └─ Stream chunks → invoke content_chunk_callbacks          │
│      │                            reasoning_chunk_callbacks            │
│      ├─ If no tool_calls: return final content                        │
│      └─ If tool_calls:                                                │
│            ├─ Invoke tool_start_callbacks (tool name + args)          │
│            ├─ Execute tools in parallel                               │
│            └─ Invoke tool_result_callbacks (tool name + result)       │
└────────────────────────────┬──────────────────────────────────────────┘
                             │
              ┌──────────────┴──────────────┐
              │  Callback Chain (synchronous during step) │
              ▼                              ▼
┌─────────────────────────┐    ┌─────────────────────────────────────────┐
│ handle_content(chunk)   │    │ handle_tool_start(name, args)           │
│ • Appends to message    │    │ • Adds tool_calls entry                 │
│ • _broadcast("content")  │    │ • _broadcast("tool_start")             │
└─────────────────────────┘    └─────────────────────────────────────────┘

┌─────────────────────────┐    ┌─────────────────────────────────────────┐
│ handle_reasoning(chunk) │    │ handle_tool_result(name, args)          │
│ • Appends to message    │    │ • Updates tool status to completed      │
│ • _broadcast("reasoning")│   │ • Replaces message index                │
└─────────────────────────┘    │ • _broadcast("tool_result")             │
                               └─────────────────────────────────────────┘
              │                              │
              └──────────────┬─────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 4. SSE BROADCAST (_broadcast to all client queues)                      │
│    All connected SSE clients receive the same events                   │
└────────────────────────────┬──────────────────────────────────────────┘
                             │
┌────────────────────────────▼──────────────────────────────────────────┐
│ 5. SSE STREAM (chat.py → GET /chats/{id}/stream)                        │
│    • Send catchup event with current interim_messages                  │
│    • Loop: client_queue.get() → yield SSE event to client               │
│    • On disconnect: active_run.remove_client(queue)                    │
└────────────────────────────┬──────────────────────────────────────────┘
                             │
┌────────────────────────────▼──────────────────────────────────────────┐
│ 6. FRONTEND SSE HANDLER (chat-context.tsx)                             │
│    • catchup: Initialize activeRunRef                                  │
│    • content: Append to message.content                               │
│    • reasoning: Append to message.reasoning_content                   │
│    • tool_start: Push to tool_calls array with status='running'       │
│    • tool_result: Update tool status, replace index with full message │
│    • 10fps throttle: setDisplayActiveMessages() → React re-render     │
└────────────────────────────┬──────────────────────────────────────────┘
                             │
┌────────────────────────────▼──────────────────────────────────────────┐
│ 7. RENDER (message-bubble.tsx)                                        │
│    • role=assistant: Markdown content + collapsible reasoning         │
│                          + tool call badges (spinner/checkmark)        │
│    • role=tool: Card with tool name and result content                │
│    • role=user: Right-aligned dark bubble with markdown               │
└─────────────────────────────────────────────────────────────────────────┘
                             │
┌────────────────────────────▼──────────────────────────────────────────┐
│ 8. PERSISTENCE (background task after step completes)                  │
│    • Extract new messages from agent.memory.messages                   │
│    • Write ChatMessage records to DB                                   │
│    • Save clipboard state to ChatSession                               │
│    • Set is_running = False                                            │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 6. SSE Event Reference

| Event | Direction | Payload | Effect on Frontend |
|-------|-----------|---------|-------------------|
| `catchup` | Server → Client | `{interim_messages: ChatMessage[]}` | Initializes `activeRunRef` with all messages so far |
| `content` | Server → Client | `{data: string, index: number}` | Appends text to `message[index].content` |
| `reasoning` | Server → Client | `{data: string, index: number}` | Appends text to `message[index].reasoning_content` |
| `tool_start` | Server → Client | `{data: {name, args}, index: number}` | Pushes tool to `message[index].tool_calls` with `status: 'running'` |
| `tool_result` | Server → Client | `{data: {role, name, content}, index: number}` | Replaces `message[index]` with full tool message |

---

## 7. Data Structures

### Frontend ChatMessage (`myproject-frontend/types/chat.ts`)

```typescript
interface ChatMessage {
  role: 'user' | 'assistant' | 'tool' | 'system';
  content: string;
  reasoning_content?: string;
  tool_calls?: Array<{
    name: string;
    args: Record<string, any>;
    status: 'running' | 'completed';
  }>;
  name?: string;  // Present when role is 'tool'
}
```

### Backend ChatSession Model (`myproject-server/src/myproject_server/models/chat.py`)

- `id`, `user_id`, `agent_id`, `title`, `is_running`, `clipboard_state`, `created_at`, `updated_at`
- `is_running` is a concurrency lock to prevent multiple simultaneous agent runs

### AgentMemory (`myproject-core/src/myproject_core/agent_memory.py`)

- `messages: list[dict]` — conversation history, persisted to DB
- `agent_clipboard: AgentClipboard` — ephemeral in-memory context (files, pinned entities, tool results)

---

## 8. Key Integration Points

### Where to add new SSE events

If you need to send additional event types (e.g., a phase/state indicator), the changes span three layers:

1. **Agent core** (`agent.py`): Invoke the new callback at the appropriate point in `step()`
2. **ActiveRun** (`chat_manager.py`): Add a new `handle_*` method that broadcasts the event
3. **Frontend** (`chat-context.tsx`): Add a new `addEventListener` for the event type

### Where to modify message accumulation logic

The `ActiveRun.messages` list is the authoritative in-progress message state. Modifying how interim messages are structured happens in `chat_manager.py` ActiveRun methods.

### Where persistence happens

Message persistence to the database happens exclusively in the background task after `agent.step()` completes (in `chat.py` lines 186-199). The SSE stream is for real-time display only — it does not write to the database.