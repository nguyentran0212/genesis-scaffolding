# LLM Provider Abstraction

## Overview

The LLM layer provides a **provider-agnostic interface** for calling language models. A single entry point — `get_llm_response()` — routes requests to the appropriate implementation based on the provider. This makes it trivial to swap providers or add support for new ones.

```
┌─────────────────────────────────────────────────────────────┐
│                      get_llm_response()                       │
│         (myproject_core/llm/__init__.py)                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
          ┌────────────┴────────────┐
          │  is_anthropic_provider   │
          │     (provider.name ==    │
          │       "minimax")        │
          └────────────┬────────────┘
                       │
           ┌──────────┴──────────┐
           │     Yes               │ No
           ▼                       ▼
    ┌──────────────┐       ┌──────────────┐
    │ _call_anthropic      │ get_llm_response  │
    │ (Anthropic SDK)      │ (LiteLLM)        │
    └──────────────┘       └──────────────┘
```

---

## Entry Point: `get_llm_response()`

**File:** `myproject_core/src/myproject_core/llm/__init__.py`

```python
async def get_llm_response(
    llm_model_config: LLMModelConfig,
    provider_config: LLMProvider,
    messages: list[Any],
    stream: bool = False,
    content_chunk_callbacks: list[StreamCallback] | None = None,
    reasoning_chunk_callbacks: list[StreamCallback] | None = None,
    tools: list[Any] | None = None,
) -> LLMResponse:
```

**Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `llm_model_config` | `LLMModelConfig` | Model name and per-call params (temperature, max_tokens, etc.) |
| `provider_config` | `LLMProvider` | Provider name, base_url, api_key |
| `messages` | `list[dict]` | Messages in OpenAI format (`{role, content}`) |
| `stream` | `bool` | Whether to stream the response |
| `content_chunk_callbacks` | `list[StreamCallback]` | Called for each content chunk |
| `reasoning_chunk_callbacks` | `list[StreamCallback]` | Called for each reasoning/thinking chunk |
| `tools` | `list[dict]` | Tool definitions in OpenAI function-calling format |

**Returns:** `LLMResponse(content, reasoning_content, tool_calls)`

---

## Provider Routing

**File:** `myproject_core/src/myproject_core/llm/_base.py`

Routing is intentionally simple:

```python
def is_anthropic_provider(provider_config: LLMProvider) -> bool:
    return provider_config.name == "minimax"
```

- **`minimax` → Anthropic SDK** — MiniMax is Anthropic-compatible but has incompatibilities with LiteLLM's handling of extended thinking
- **Everything else → LiteLLM** — OpenAI-compatible providers (OpenRouter, local llama.cpp, LM Studio, etc.)

---

## LiteLLM Implementation

**File:** `myproject_core/src/myproject_core/llm/_litellm.py`

Used for OpenAI-compatible providers. Delegates to `litellm.acompletion()`:

```python
await acompletion(
    api_base=provider_config.base_url,
    api_key=provider_config.api_key,
    model=f"{provider_config.name}/{llm_model_config.model}",
    messages=messages,
    stream=stream,
    tools=tools,
    **llm_model_config.params,
)
```

**Key capabilities:**
- Handles streaming with callbacks for both content and `reasoning_content` (OpenAI's extended reasoning)
- Parses tool calls from streaming chunks
- `stream_options={"include_usage": True}` enables usage metadata

---

## Anthropic SDK Implementation

**File:** `myproject_core/src/myproject_core/llm/_anthropic.py`

Used for MiniMax and similar Anthropic-compatible providers that don't work well with LiteLLM.

**Message format conversion** — OpenAI format differs from Anthropic's in several ways:

| OpenAI | Anthropic |
|---|---|
| `role: system` | Extracted to separate `system` param |
| `content: str` | `content: [{"type": "text", "text": "..."}]` |
| `role: tool` | `role: user` with `{"type": "tool_result", ...}` blocks |
| `tool_calls: [...]` | `content: [{"type": "tool_use", ...}]` blocks |
| `parameters` in tools | `input_schema` in tools |

Two conversion functions handle this:

- `_convert_messages_for_anthropic()` — splits system messages out, wraps content in blocks, converts tool roles
- `_convert_tools_for_anthropic()` — maps `parameters` → `input_schema`

**Thinking block support** — When a provider emits `thinking` blocks (extended reasoning), they are streamed via `reasoning_chunk_callbacks` and accumulated in `reasoning_content`.

---

## Data Schemas

### `LLMProvider`
```python
class LLMProvider(BaseModel):
    name: str | None = "openrouter"
    base_url: str | None = "https://openrouter.ai/api/v1"
    api_key: str
```

Configured per-user via the frontend. Users select which provider to use when creating a chat session.

### `LLMModelConfig`
```python
class LLMModelConfig(BaseModel):
    model: str                          # e.g., "anthropic/claude-3-5-sonnet"
    params: dict[str, Any] = {}        # max_tokens, temperature, reasoning_effort, etc.
```

Per-call parameters live in `params` — things like `max_tokens`, `temperature`, or `reasoning_effort`.

### `LLMResponse`
```python
class LLMResponse(BaseModel):
    content: str                       # Text response
    reasoning_content: str              # Extended thinking/reasoning (if any)
    tool_calls: list[ToolCall] = []    # Structured tool call requests
```

### `ToolCall`
```python
class ToolCall(BaseModel):
    id: str            # Unique call ID (matches tool_use_id in tool results)
    function_name: str # Tool name
    arguments: str     # Raw JSON string of arguments
```

---

## Streaming and Callbacks

Both implementations support streaming via callbacks. The callback signature is:

```python
StreamCallback = Callable[[str], Awaitable[None]]
```

Three separate callback streams:

| Callback | Called when |
|---|---|
| `content_chunk_callbacks` | Each text content delta arrives |
| `reasoning_chunk_callbacks` | Each reasoning/thinking delta arrives |
| (tool callbacks in agent loop) | Tool starts and completes |

Callbacks are `asyncio.gather`-ed for parallel invocation, ensuring minimal latency between receiving a chunk and notifying all subscribers.

---

## Key Design Decisions

1. **Single entry point** — `get_llm_response()` hides all routing. Adding a new provider implementation only requires adding a new module and updating the router.
2. **OpenAI format internally** — All message formatting is OpenAI-style internally. Provider-specific conversions happen at the boundary (in `_litellm.py` or `_anthropic.py`), keeping the core logic provider-agnostic.
3. **MiniMax as the Anthropic edge case** — MiniMax is the only current exception to the LiteLLM default. It uses the Anthropic SDK because LiteLLM's handling of MiniMax's extended thinking blocks is unreliable.
4. **Reasoning as a first-class output** — `reasoning_content` is a top-level field in `LLMResponse`, not buried in metadata. This makes it easy for the agent loop to inject reasoning into SSE streams or clipboard.
5. **Raw JSON strings for tool arguments** — `ToolCall.arguments` stores the raw JSON string. Parsing is deferred to the tool execution layer, which handles JSON decode errors gracefully.

---

## Critical Files

| File | Purpose |
|---|---|
| `myproject-core/src/myproject_core/llm/__init__.py` | `get_llm_response()` entry point and routing |
| `myproject-core/src/myproject_core/llm/_base.py` | `is_anthropic_provider()` |
| `myproject-core/src/myproject_core/llm/_litellm.py` | LiteLLM implementation for OpenAI-compatible providers |
| `myproject-core/src/myproject_core/llm/_anthropic.py` | Anthropic SDK implementation for MiniMax |
| `myproject-core/src/myproject_core/schemas.py` | `LLMProvider`, `LLMModelConfig`, `LLMResponse`, `ToolCall` |
| `myproject-server/src/myproject_server/schemas/llm_config.py` | `LLMConfigRead` for frontend API |
