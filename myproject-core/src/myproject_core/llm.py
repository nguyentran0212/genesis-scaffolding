import asyncio
import json
from typing import Any, cast

import anthropic
from anthropic import AsyncAnthropic
import litellm
from litellm import CustomStreamWrapper, ModelResponse, acompletion
from litellm.types.utils import Choices, StreamingChoices

from .schemas import LLMModelConfig, LLMProvider, LLMResponse, StreamCallback, ToolCall

litellm.suppress_debug_info = True  # Silences provider suggestion logs


def _is_minimax_provider(provider_config: LLMProvider) -> bool:
    """Check if this provider should use the Anthropic SDK directly."""
    return provider_config.name == "minimax"


def _convert_tools_for_anthropic(tools: list[dict]) -> list[dict]:
    """Convert OpenAI function-calling format to Anthropic tool format.

    Anthropic uses 'input_schema' instead of 'parameters' for the JSON Schema.
    The JSON Schema itself remains unchanged.
    """
    if not tools:
        return []

    anthropic_tools = []
    for tool in tools:
        func = tool.get("function", {})
        anthropic_tools.append(
            {
                "type": "tool",
                "name": func["name"],
                "description": func.get("description", ""),
                "input_schema": func.get("parameters", {}),
            },
        )
    return anthropic_tools


def _convert_messages_for_anthropic(messages: list[dict]) -> tuple[list[dict], str | None]:
    """Convert message list to Anthropic API format.

    Anthropic expects message content as {"type": "text", "text": "..."} blocks
    instead of plain strings. System messages are extracted and returned separately.

    Returns:
        Tuple of (anthropic_messages, system_prompt) where system_prompt is the
        combined content of any system messages, or None if no system messages.
    """
    anthropic_messages = []
    system_parts = []

    for msg in messages:
        role = msg.get("role")
        content = msg.get("content", "")

        # System messages - extract to separate system_prompt (Anthropic doesn't accept role=system in messages array)
        if role == "system":
            system_parts.append(content)
            continue

        # Tool messages become user messages with tool_result content blocks
        # Per Anthropic spec: tool results are sent as role=user with tool_result content
        if role == "tool":
            tool_use_id = msg.get("tool_call_id", "")
            tool_content = content
            print(
                f"[TOOL RESULT DEBUG] Converting tool message: tool_use_id={tool_use_id}, content={tool_content[:100]}..."
            )
            anthropic_messages.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_use_id,
                            "content": tool_content,
                        },
                    ],
                },
            )
            continue

        # Assistant messages may have tool_calls that need to be converted to tool_use blocks
        if role == "assistant" and msg.get("tool_calls"):
            tool_calls = msg["tool_calls"]
            content_blocks = []
            if content:
                content_blocks.append({"type": "text", "text": content})
            for tc in tool_calls:
                func = tc.get("function", {})
                args = func.get("arguments", "{}")
                # Parse arguments JSON if string
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        args = {}
                content_blocks.append(
                    {
                        "type": "tool_use",
                        "id": tc.get("id", ""),
                        "name": func.get("name", ""),
                        "input": args,
                    }
                )
            anthropic_messages.append({"role": role, "content": content_blocks})
        # Regular messages - content can be string or list of blocks
        elif isinstance(content, str):
            anthropic_messages.append({"role": role, "content": [{"type": "text", "text": content}]})
        else:
            # Already in block format, pass through
            anthropic_messages.append({"role": role, "content": content})

    # Combine all system messages
    system_prompt = "\n\n".join(system_parts) if system_parts else None

    print(
        f"[MESSAGE DEBUG] Converted {len(anthropic_messages)} messages, system_prompt length: {len(system_prompt) if system_prompt else 0}"
    )
    for i, msg in enumerate(anthropic_messages):
        role = msg.get("role")
        content = msg.get("content", "")
        if isinstance(content, list):
            types = [c.get("type") for c in content if isinstance(c, dict)]
            print(f"[MESSAGE DEBUG]   [{i}] role={role}, content_types={types}")
        else:
            print(f"[MESSAGE DEBUG]   [{i}] role={role}, content={str(content)[:50]}...")

    return anthropic_messages, system_prompt


async def _call_anthropic(
    llm_model_config: LLMModelConfig,
    provider_config: LLMProvider,
    messages: list[Any],
    stream: bool,
    content_chunk_callbacks: list[StreamCallback] | None,
    reasoning_chunk_callbacks: list[StreamCallback] | None,
    tools: list[Any] | None,
) -> LLMResponse:
    """Use official Anthropic SDK for Minimax and similar providers."""
    print("REACH CALL ANTHROPIC")
    print(provider_config)
    client = anthropic.Anthropic(
        api_key=provider_config.api_key,
        base_url=str(provider_config.base_url) if provider_config.base_url else None,
    )

    # Convert messages to Anthropic format - returns (messages, system_prompt)
    anthropic_messages, extracted_system = _convert_messages_for_anthropic(messages)

    # Convert tools to Anthropic format
    anthropic_tools = _convert_tools_for_anthropic(tools) if tools else None

    # Build params
    params: dict[str, Any] = {
        "model": llm_model_config.model,
        "messages": anthropic_messages,
        "max_tokens": llm_model_config.params.get("max_tokens", 4096),
    }
    if anthropic_tools:
        params["tools"] = anthropic_tools

    # Handle additional params - system from model config takes priority
    if "system" in llm_model_config.params:
        params["system"] = llm_model_config.params["system"]
    elif extracted_system:
        params["system"] = extracted_system

    if "temperature" in llm_model_config.params:
        params["temperature"] = llm_model_config.params["temperature"]

    print(f"[DEBUG] Minimax params: model={params['model']}, max_tokens={params['max_tokens']}")
    print(f"[DEBUG] First message: {params['messages'][0] if params['messages'] else 'NONE'}")
    print(f"[DEBUG] System: {params.get('system', 'NONE')[:100]}...")
    print(f"[DEBUG] Full messages being sent: {params['messages']}")

    if stream:
        async_client = AsyncAnthropic(
            api_key=provider_config.api_key,
            base_url=str(provider_config.base_url) if provider_config.base_url else None,
        )
        return await _parse_anthropic_stream(
            async_client,
            params,
            content_chunk_callbacks,
            reasoning_chunk_callbacks,
        )
    return _parse_anthropic_nonstream(client.messages.create(**params))


def _parse_anthropic_nonstream(response: anthropic.types.Message) -> LLMResponse:
    """Parse non-streaming Anthropic response."""
    full_content = ""
    full_reasoning_content = ""
    tool_calls_list: list[dict[str, Any]] = []

    for block in response.content:
        if block.type == "text":
            full_content += block.text
        elif block.type == "thinking":
            full_reasoning_content += block.thinking
        elif block.type == "tool_use":
            # Non-streaming tool_use blocks have id, name, input directly (no index)
            args_dict = block.input if isinstance(block.input, dict) else {}
            tool_calls_list.append(
                {
                    "id": block.id,
                    "name": block.name,
                    "args": args_dict,
                },
            )

    final_tool_calls = []
    for tc in tool_calls_list:
        args_str = tc.get("args", {})
        if isinstance(args_str, dict):
            args_str = json.dumps(args_str)
        final_tool_calls.append(
            ToolCall(
                id=tc["id"],
                function_name=tc["name"],
                arguments=str(args_str),
            ),
        )

    return LLMResponse(
        content=full_content,
        reasoning_content=full_reasoning_content,
        tool_calls=final_tool_calls,
    )


async def _parse_anthropic_stream(
    client: AsyncAnthropic,
    params: dict[str, Any],
    content_chunk_callbacks: list[StreamCallback] | None,
    reasoning_chunk_callbacks: list[StreamCallback] | None,
) -> LLMResponse:
    """Parse streaming Anthropic response using async iteration for real-time callbacks.

    Per Anthropic streaming spec:
    - text comes through content_block_delta with delta.type == "text_delta"
    - thinking comes through content_block_delta with delta.type == "thinking_delta"
    - tool args come through content_block_delta with delta.type == "input_json_delta"
    - signature_delta events should be ignored
    """
    full_content = ""
    full_reasoning_content = ""
    tool_calls_dict: dict[int, dict[str, Any]] = {}

    async with client.messages.stream(**params) as stream:
        async for event in stream:
            event_type = getattr(event, "type", None)

            # Debug: log all event types we receive
            print(f"[STREAM DEBUG] Received event: {event_type}")

            # Debug: log all event types and content_block info
            if event_type in ("content_block_start", "content_block_delta", "text", "thinking"):
                content_block = getattr(event, "content_block", None)
                print(f"[STREAM DEBUG]   index={getattr(event, 'index', 'N/A')}")
                if content_block:
                    print(
                        f"[STREAM DEBUG]   content_block type={getattr(content_block, 'type', 'N/A')}, id={getattr(content_block, 'id', 'N/A')}, name={getattr(content_block, 'name', 'N/A')}"
                    )
                if event_type == "content_block_delta":
                    delta = getattr(event, "delta", None)
                    if delta:
                        print(
                            f"[STREAM DEBUG]   delta type={getattr(delta, 'type', 'N/A')}, text={getattr(delta, 'text', 'N/A')[:50] if getattr(delta, 'text', None) else 'N/A'}"
                        )

            # Handle content block start - initialize tool use tracking
            if event_type == "content_block_start":
                idx = event.index  # type: ignore
                content_block = getattr(event, "content_block", None)
                if content_block and getattr(content_block, "type", None) == "tool_use":
                    tool_id = getattr(content_block, "id", "") or ""
                    tool_name = getattr(content_block, "name", "") or ""
                    print(
                        f"[TOOL DEBUG] content_block_start: idx={idx}, tool_id={tool_id}, tool_name={tool_name}"
                    )
                    tool_calls_dict[idx] = {
                        "id": tool_id,
                        "name": tool_name,
                        "args": "",
                    }

            # Handle content block delta - this is where ALL content arrives
            elif event_type == "content_block_delta":
                delta = getattr(event, "delta", None)
                if not delta:
                    continue

                delta_type = getattr(delta, "type", None)
                idx = event.index  # type: ignore

                # Text content
                if delta_type == "text_delta":
                    text_value = getattr(delta, "text", "") or ""
                    if text_value:
                        full_content += text_value
                        if content_chunk_callbacks:
                            await asyncio.gather(*[cb(text_value) for cb in content_chunk_callbacks])

                # Thinking content
                elif delta_type == "thinking_delta":
                    thinking_value = getattr(delta, "thinking", "") or ""
                    if thinking_value:
                        full_reasoning_content += thinking_value
                        if reasoning_chunk_callbacks:
                            await asyncio.gather(*[cb(thinking_value) for cb in reasoning_chunk_callbacks])

                # Tool use arguments (partial JSON)
                elif delta_type == "input_json_delta":
                    partial_json = getattr(delta, "partial_json", "") or ""
                    if partial_json:
                        if idx not in tool_calls_dict:
                            tool_calls_dict[idx] = {"id": "", "name": "", "args": ""}
                        tool_calls_dict[idx]["args"] = tool_calls_dict[idx].get("args", "") + partial_json

                # signature_delta - ignore, used for integrity verification only

    # Build final tool calls
    final_tool_calls = []
    for idx, tc in sorted(tool_calls_dict.items()):
        args_str = tc.get("args", "")
        if isinstance(args_str, dict):
            args_str = json.dumps(args_str)
        print(
            f"[TOOL DEBUG] Building ToolCall: id={tc.get('id', '')}, name={tc.get('name', '')}, args={args_str[:100]}..."
        )
        final_tool_calls.append(
            ToolCall(
                id=tc.get("id", ""),
                function_name=tc.get("name", ""),
                arguments=args_str,
            )
        )

    print(
        f"[TOOL DEBUG] Final tool_calls: {[{'id': tc.id, 'name': tc.function_name} for tc in final_tool_calls]}"
    )
    print(f"[TOOL DEBUG] Full tool_calls_dict: {tool_calls_dict}")

    return LLMResponse(
        content=full_content,
        reasoning_content=full_reasoning_content,
        tool_calls=final_tool_calls,
    )


async def get_llm_response(
    llm_model_config: LLMModelConfig,
    provider_config: LLMProvider,
    messages: list[Any],
    stream=False,
    content_chunk_callbacks: list[StreamCallback] | None = None,
    reasoning_chunk_callbacks: list[StreamCallback] | None = None,
    tools: list[Any] | None = None,
) -> LLMResponse:
    """Executes a completion request against an LLM and handles both static and streaming outputs. This function is async by default.

    The caller receives full content and reasoning content from the LLM regardless of whether they stream or not.

    The caller can pass callback functions to handle each of the content and reasoning chunk coming from the model (e.g., to display to UI)

    Args:
        llm_model_config: An LLMModel configuration object containing details about the models to call and additional params.
        provider_config: base url and api key of the model provider
        messages: A list of message dictionaries (role/content) representing the conversation history.
        stream: If True, the function iterates over the response stream and triggers callbacks. Defaults to False.
        content_chunk_callbacks: An optional list of async functions triggered every time a new 'content' text chunk is received during streaming. Useful for real-time UI updates.
        reasoning_chunk_callbacks: An optional list of async functions triggered every time a 'reasoning_content' chunk (Chain-of-Thought) is received. Used for displaying the model's internal logic as it generates.

    Returns:
        LLMResponse: A custom object containing the fully accumulated 'content' and 'reasoning_content'.

    Raises:
        RuntimeError: If the returned LiteLLM object does not match the requested 'stream' mode.
        ValueError: If the provider config does not match the model config

    """
    # Route to Anthropic SDK for minimax provider
    if _is_minimax_provider(provider_config):
        return await _call_anthropic(
            llm_model_config,
            provider_config,
            messages,
            stream,
            content_chunk_callbacks,
            reasoning_chunk_callbacks,
            tools,
        )

    # Default: use LiteLLM for OpenAI-compatible providers
    response: Any = await acompletion(
        # base_url=provider_config.base_url,
        api_base=provider_config.base_url,
        api_key=provider_config.api_key,
        model=f"{provider_config.name}/{llm_model_config.model}",
        messages=messages,
        stream=stream,
        stream_options={"include_usage": True},
        tools=tools,
        extra_headers={"Authorization": f"Bearer {provider_config.api_key}"},
        **llm_model_config.params,
    )

    full_content = ""
    full_reasoning_content = ""
    tool_calls_dict = {}

    if stream:
        if not isinstance(response, CustomStreamWrapper):
            raise RuntimeError("Expected a stream from litellm but didn't get one.")
        full_content = ""
        full_reasoning_content = ""
        async for chunk in response:
            # This cast prevents pyright from assign the type of choice correctly to streaming choice
            choice = cast("StreamingChoices", chunk.choices[0])

            # Handle Content Chunk
            content = getattr(choice.delta, "content", "") or ""
            if content:
                full_content += content
                if content_chunk_callbacks:
                    await asyncio.gather(*[cb(content) for cb in content_chunk_callbacks])

            # Handle Reasoning Chunk
            reasoning = getattr(choice.delta, "reasoning_content", "") or ""
            if reasoning:
                full_reasoning_content += reasoning
                if reasoning_chunk_callbacks:
                    await asyncio.gather(*[cb(reasoning) for cb in reasoning_chunk_callbacks])

            # Handle tool call chunks
            tool_calls = getattr(choice.delta, "tool_calls", None)
            if tool_calls:
                for tc in tool_calls:
                    idx = tc.index
                    if idx not in tool_calls_dict:
                        tool_calls_dict[idx] = {"id": "", "name": "", "args": ""}
                    if tc.id:
                        tool_calls_dict[idx]["id"] += tc.id
                    if tc.function.name:
                        tool_calls_dict[idx]["name"] += tc.function.name
                    if tc.function.arguments:
                        tool_calls_dict[idx]["args"] += tc.function.arguments

    else:
        if not isinstance(response, ModelResponse):
            raise RuntimeError("Expected a ModelResponse from litellm but didn't get one.")

        # This cast prevents pyright from incorrectly assign the type of choice to be StreamingChoice
        choices = response.choices[0]
        choices = cast("Choices", choices)

        full_content = getattr(choices.message, "content", full_content)
        full_reasoning_content = getattr(choices.message, "reasoning_content", full_reasoning_content)

        tool_calls = getattr(choices.message, "tool_calls", None)
        if tool_calls:
            for i, tc in enumerate(tool_calls):
                tool_calls_dict[i] = {
                    "id": getattr(tc, "id", ""),
                    "name": getattr(tc.function, "name", ""),
                    "args": getattr(tc.function, "arguments", ""),
                }
    final_tool_calls = [
        ToolCall(id=v["id"], function_name=v["name"], arguments=v["args"]) for v in tool_calls_dict.values()
    ]
    return LLMResponse(
        content=full_content,
        reasoning_content=full_reasoning_content,
        tool_calls=final_tool_calls,
    )
