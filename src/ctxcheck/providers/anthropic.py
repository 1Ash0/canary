"""Anthropic Messages API adapter (formats verified from the docs, see the provider-formats note).

`build_request` and `parse_response` are pure so they can be tested without HTTP. `complete` adds
the key, posts through the shared retrying layer and parses the reply into a `ModelResponse`.

Two deliberate omissions: no `temperature`/`top_p`/`top_k` unless the caller passes one (newer
Claude models reject non-default values with a 400), and no system role in `messages` (the system
prompt is a top-level field).
"""

from __future__ import annotations

import time
from collections.abc import Callable, Sequence
from typing import Any

import httpx

from ctxcheck.harness.types import Message, ModelResponse, ToolCall, ToolSpec
from ctxcheck.providers._http import ProviderError, post_json, read_key

URL = "https://api.anthropic.com/v1/messages"
VERSION = "2023-06-01"
PASSTHROUGH_PARAMS = ("temperature",)  # sent only if the caller sets them


def _blocks_for(m: Message) -> tuple[str, list[dict[str, Any]]]:
    """(api role, content blocks) for one of our messages. Tool results travel as user blocks."""
    if m.role == "tool":
        block: dict[str, Any] = {
            "type": "tool_result", "tool_use_id": m.call_id, "content": m.content,
        }
        if m.is_error:
            block["is_error"] = True
        return "user", [block]
    if m.role == "assistant":
        if m.tool_call is not None:
            blocks: list[dict[str, Any]] = []
            if m.lead_in:
                blocks.append({"type": "text", "text": m.lead_in})
            blocks.append({"type": "tool_use", "id": m.tool_call.id, "name": m.tool_call.name,
                           "input": m.tool_call.args})
            return "assistant", blocks
        return "assistant", [{"type": "text", "text": m.content}] if m.content else []
    return "user", [{"type": "text", "text": m.content}] if m.content else []


def build_request(
    model: str,
    max_tokens: int,
    messages: Sequence[Message],
    tools: Sequence[ToolSpec],
    params: dict[str, Any],
) -> dict[str, Any]:
    system = "\n\n".join(m.content for m in messages if m.role == "system")
    turns: list[dict[str, Any]] = []
    for m in messages:
        if m.role == "system":
            continue
        role, blocks = _blocks_for(m)
        if not blocks:
            continue
        if turns and turns[-1]["role"] == role:  # the API combines consecutive turns; do it here
            turns[-1]["content"].extend(blocks)
        else:
            turns.append({"role": role, "content": list(blocks)})
    for turn in turns:  # tool_result blocks must lead a user message
        turn["content"].sort(key=lambda b: b["type"] != "tool_result")

    body: dict[str, Any] = {"model": model, "max_tokens": max_tokens, "messages": turns}
    if system:
        body["system"] = system
    if tools:
        body["tools"] = [
            {"name": t.name, "description": t.description, "input_schema": t.input_schema}
            for t in tools
        ]
        body["tool_choice"] = {"type": "auto", "disable_parallel_tool_use": True}
    for key in PASSTHROUGH_PARAMS:
        if key in params:
            body[key] = params[key]
    return body


def _int(value: Any) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def parse_response(data: dict[str, Any]) -> ModelResponse:
    content = data.get("content")
    if not isinstance(content, list):
        raise ProviderError("anthropic reply has no content list")
    text = "".join(b.get("text", "") for b in content if b.get("type") == "text")
    uses = [b for b in content if b.get("type") == "tool_use"]
    call = None
    extra: dict[str, Any] = {"stop_reason": data.get("stop_reason")}
    if uses:
        first = uses[0]
        args = first.get("input")
        call = ToolCall(str(first.get("id")), str(first.get("name")),
                        args if isinstance(args, dict) else {})
        if len(uses) > 1:
            extra["dropped_tool_calls"] = len(uses) - 1
    usage = data.get("usage") or {}
    return ModelResponse(
        text=text,
        tool_call=call,
        input_tokens=_int(usage.get("input_tokens")) or 0,
        output_tokens=_int(usage.get("output_tokens")) or 0,
        cache_read_input_tokens=_int(usage.get("cache_read_input_tokens")),
        cache_creation_input_tokens=_int(usage.get("cache_creation_input_tokens")),
        model_id=str(data.get("model", "unknown")),
        extra=extra,
    )


class AnthropicProvider:
    def __init__(
        self,
        model: str,
        *,
        max_tokens: int = 1024,
        api_key_env: str = "ANTHROPIC_API_KEY",
        url: str = URL,
        client: httpx.Client | None = None,
        max_attempts: int = 4,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.model = model
        self.max_tokens = max_tokens
        self._api_key_env = api_key_env
        self._url = url
        self._client = client or httpx.Client(timeout=60.0)
        self._max_attempts = max_attempts
        self._sleep = sleep

    def __repr__(self) -> str:  # never includes anything secret
        return f"AnthropicProvider(model={self.model!r})"

    def complete(
        self,
        messages: Sequence[Message],
        tools: Sequence[ToolSpec],
        params: dict[str, Any],
        trial_index: int,
    ) -> ModelResponse:
        key = read_key(self._api_key_env)  # read now, never stored
        headers = {"Content-Type": "application/json", "anthropic-version": VERSION,
                   "X-Api-Key": key}
        limit = int(params.get("max_tokens", self.max_tokens))  # a per-call cap wins
        body = build_request(self.model, limit, messages, tools, params)
        data = post_json(self._client, self._url, headers, body,
                         max_attempts=self._max_attempts, sleep=self._sleep)
        return parse_response(data)
