"""OpenAI-compatible chat completions adapter (covers OpenAI and many hosted and local servers).

Formats verified from the OpenAI function-calling guide (see the provider-formats note). Differences
from the Anthropic adapter that matter: the system prompt is a message with role "system"; a tool
call's `arguments` arrive as a JSON *string*; results go back as role "tool" messages; usage is
`prompt_tokens`/`completion_tokens`, and no cache fields are reported (the cached-token detail field
was not verified, so it is left None rather than guessed).
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable, Sequence
from typing import Any

import httpx

from ctxcheck.harness.types import BAD_ARGS_KEY, Message, ModelResponse, ToolCall, ToolSpec
from ctxcheck.providers._http import ProviderError, post_json, read_key

DEFAULT_BASE_URL = "https://api.openai.com/v1"
# sent only if the caller sets them; reasoning_effort is documented for gpt-oss on Groq
PASSTHROUGH_PARAMS = ("temperature", "reasoning_effort")


def _convert(m: Message) -> dict[str, Any] | None:
    if m.role == "tool":
        return {"role": "tool", "tool_call_id": m.call_id, "content": m.content}
    if m.role == "assistant" and m.tool_call is not None:
        call = m.tool_call
        return {
            "role": "assistant",
            "content": m.lead_in or None,
            "tool_calls": [{
                "id": call.id, "type": "function",
                "function": {"name": call.name, "arguments": json.dumps(call.args, sort_keys=True)},
            }],
        }
    if not m.content:
        return None
    return {"role": m.role, "content": m.content}


def build_request(
    model: str,
    max_tokens: int,
    max_tokens_field: str,
    messages: Sequence[Message],
    tools: Sequence[ToolSpec],
    params: dict[str, Any],
    limit_to_one_tool_call: bool = True,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "model": model,
        max_tokens_field: max_tokens,
        "messages": [c for m in messages if (c := _convert(m)) is not None],
    }
    if tools:
        body["tools"] = [
            {"type": "function", "function": {
                "name": t.name, "description": t.description, "parameters": t.input_schema}}
            for t in tools
        ]
        if limit_to_one_tool_call:  # not every compatible server accepts this parameter
            body["parallel_tool_calls"] = False
    for key in PASSTHROUGH_PARAMS:
        if key in params:
            body[key] = params[key]
    return body


def _int(value: Any) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def parse_response(data: dict[str, Any]) -> ModelResponse:
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
        raise ProviderError("reply has no choices")
    message = choices[0].get("message") or {}
    text = message.get("content") or ""
    raw_calls = message.get("tool_calls") or []
    extra: dict[str, Any] = {"finish_reason": choices[0].get("finish_reason")}

    call = None
    if raw_calls:
        first = raw_calls[0]
        fn = first.get("function") or {}
        raw_args = fn.get("arguments", "")
        try:
            args = json.loads(raw_args) if raw_args else {}
            if not isinstance(args, dict):
                raise ValueError("not an object")
        except ValueError:
            args = {BAD_ARGS_KEY: str(raw_args)[:300]}  # the dispatcher reports it to the model
        call = ToolCall(str(first.get("id")), str(fn.get("name")), args)
        if len(raw_calls) > 1:
            extra["dropped_tool_calls"] = len(raw_calls) - 1

    usage = data.get("usage") or {}
    return ModelResponse(
        text=text if isinstance(text, str) else "",
        tool_call=call,
        input_tokens=_int(usage.get("prompt_tokens")),
        output_tokens=_int(usage.get("completion_tokens")),
        model_id=str(data.get("model", "unknown")),
        extra=extra,
    )


class OpenAICompatProvider:
    def __init__(
        self,
        model: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        api_key_env: str = "OPENAI_API_KEY",
        max_tokens: int = 1024,
        max_tokens_field: str = "max_tokens",  # some models want "max_completion_tokens"
        limit_to_one_tool_call: bool = True,  # send parallel_tool_calls=false; off if unsupported
        client: httpx.Client | None = None,
        max_attempts: int = 4,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.model = model
        self._url = base_url.rstrip("/") + "/chat/completions"
        self._api_key_env = api_key_env
        self._max_tokens = max_tokens
        self._max_tokens_field = max_tokens_field
        self._limit_to_one = limit_to_one_tool_call
        self._client = client or httpx.Client(timeout=60.0)
        self._max_attempts = max_attempts
        self._sleep = sleep

    def __repr__(self) -> str:  # never includes anything secret
        return f"OpenAICompatProvider(model={self.model!r}, url={self._url!r})"

    def complete(
        self,
        messages: Sequence[Message],
        tools: Sequence[ToolSpec],
        params: dict[str, Any],
        trial_index: int,
    ) -> ModelResponse:
        key = read_key(self._api_key_env)  # read now, never stored
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {key}"}
        body = build_request(
            self.model, int(params.get("max_tokens", self._max_tokens)), self._max_tokens_field,
            messages, tools, params,
            self._limit_to_one,
        )
        data = post_json(self._client, self._url, headers, body,
                         max_attempts=self._max_attempts, sleep=self._sleep)
        return parse_response(data)
