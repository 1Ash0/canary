"""Anthropic adapter against fake replies shaped like the documented ones. No network."""

import json

import httpx
import pytest

from ctxcheck.harness.types import Message, ToolCall, ToolSpec
from ctxcheck.providers._http import MissingKey, ProviderError
from ctxcheck.providers.anthropic import AnthropicProvider, build_request, parse_response

KEY = "sk-ant-test-SECRET-1234567890"
SCHEMA = {"type": "object", "properties": {"path": {"type": "string"}}}
READ = ToolSpec("read_file", "Read a file", SCHEMA)
_ids = iter(range(10_000))


def msg(role, content="", *, origin=None, **kw) -> Message:
    return Message(f"m{next(_ids)}", role, content, origin or role, 1, 1, **kw)


def build(messages, tools=(), params=None):
    return build_request("claude-test", 256, messages, tools, params or {})


def test_system_prompt_is_top_level_and_never_a_message_role() -> None:
    body = build([msg("system", "Be brief."), msg("system", "Use tools."), msg("user", "hi")])
    assert body["system"] == "Be brief.\n\nUse tools."
    assert [t["role"] for t in body["messages"]] == ["user"]
    assert body["model"] == "claude-test" and body["max_tokens"] == 256


def test_no_system_field_when_there_is_no_system_message() -> None:
    assert "system" not in build([msg("user", "hi")])


def test_tools_use_input_schema_and_ask_for_one_call_at_a_time() -> None:
    body = build([msg("user", "hi")], tools=[READ])
    assert body["tools"] == [{"name": "read_file", "description": "Read a file",
                              "input_schema": READ.input_schema}]
    assert body["tool_choice"] == {"type": "auto", "disable_parallel_tool_use": True}


def test_no_tools_means_no_tool_choice() -> None:
    body = build([msg("user", "hi")])
    assert "tools" not in body and "tool_choice" not in body


def test_temperature_is_not_sent_unless_asked() -> None:
    assert "temperature" not in build([msg("user", "hi")])
    assert build([msg("user", "hi")], params={"temperature": 1.0})["temperature"] == 1.0
    assert "top_p" not in build([msg("user", "hi")], params={"top_p": 0.5})  # not passed through


def test_a_tool_round_trip_becomes_tool_use_then_tool_result() -> None:
    call = ToolCall("toolu_1", "read_file", {"path": "a.py"})
    turns = build([
        msg("user", "check it"),
        msg("assistant", "checking\n[tool_call ...]", call_id="toolu_1", tool_call=call,
            lead_in="checking"),
        msg("tool", "file text", call_id="toolu_1"),
    ])["messages"]
    assert turns[1] == {"role": "assistant", "content": [
        {"type": "text", "text": "checking"},
        {"type": "tool_use", "id": "toolu_1", "name": "read_file", "input": {"path": "a.py"}},
    ]}
    assert turns[2] == {"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": "toolu_1", "content": "file text"},
    ]}


def test_a_tool_call_without_lead_in_has_no_empty_text_block() -> None:
    call = ToolCall("t", "read_file", {})
    turn = build([msg("assistant", "[tool_call]", call_id="t", tool_call=call)])["messages"][0]
    assert [b["type"] for b in turn["content"]] == ["tool_use"]


def test_is_error_is_sent_only_for_failed_results() -> None:
    ok = build([msg("tool", "fine", call_id="a")])["messages"][0]["content"][0]
    bad = build([msg("tool", "boom", call_id="b", is_error=True)])["messages"][0]["content"][0]
    assert "is_error" not in ok and bad["is_error"] is True


def test_a_user_message_after_a_tool_result_is_merged_with_the_result_first() -> None:
    call = ToolCall("a", "read_file", {})
    turns = build([
        msg("user", "task"),
        msg("assistant", "[call]", call_id="a", tool_call=call),
        msg("tool", "res", call_id="a"),
        msg("user", "next task"),
    ])["messages"]
    assert [t["role"] for t in turns] == ["user", "assistant", "user"]
    assert [b["type"] for b in turns[2]["content"]] == ["tool_result", "text"]


def test_a_summary_message_is_sent_as_a_user_turn() -> None:
    turns = build([msg("user", "Summary: ...", origin="summary"), msg("assistant", "ok")])
    assert [t["role"] for t in turns["messages"]] == ["user", "assistant"]


def test_empty_messages_are_dropped() -> None:
    assert build([msg("user", ""), msg("user", "hi")])["messages"][0]["content"] == [
        {"type": "text", "text": "hi"}]


REPLY = {
    "id": "msg_1", "type": "message", "role": "assistant", "model": "claude-test-1",
    "stop_reason": "end_turn",
    "content": [{"type": "text", "text": "All done."}],
    "usage": {"input_tokens": 100, "output_tokens": 20,
              "cache_creation_input_tokens": 30, "cache_read_input_tokens": 60},
}
TOOL_REPLY = {**REPLY, "stop_reason": "tool_use", "content": [
    {"type": "text", "text": "Reading."},
    {"type": "tool_use", "id": "toolu_9", "name": "read_file", "input": {"path": "b.py"}},
]}


def test_parse_a_text_reply_with_usage_and_cache_fields() -> None:
    r = parse_response(REPLY)
    assert (r.text, r.tool_call, r.model_id) == ("All done.", None, "claude-test-1")
    assert (r.input_tokens, r.output_tokens) == (100, 20)
    assert (r.cache_read_input_tokens, r.cache_creation_input_tokens) == (60, 30)
    assert r.extra["stop_reason"] == "end_turn"


def test_parse_a_tool_call() -> None:
    r = parse_response(TOOL_REPLY)
    assert r.text == "Reading."
    assert r.tool_call == ToolCall("toolu_9", "read_file", {"path": "b.py"})


def test_two_tool_calls_take_the_first_and_record_the_rest() -> None:
    two = {**TOOL_REPLY, "content": [*TOOL_REPLY["content"],
           {"type": "tool_use", "id": "toolu_10", "name": "read_file", "input": {"path": "c.py"}}]}
    r = parse_response(two)
    assert r.tool_call.id == "toolu_9" and r.extra["dropped_tool_calls"] == 1  # type: ignore[union-attr]


def test_absent_cache_fields_are_none_not_zero() -> None:
    bare = {**REPLY, "usage": {"input_tokens": 5, "output_tokens": 2}}
    r = parse_response(bare)
    assert r.cache_read_input_tokens is None and r.cache_creation_input_tokens is None


def test_a_reply_without_content_is_a_provider_error() -> None:
    with pytest.raises(ProviderError):
        parse_response({"id": "x"})


def test_a_non_object_tool_input_becomes_empty_args_not_a_crash() -> None:
    odd = {**TOOL_REPLY, "content": [{"type": "tool_use", "id": "t", "name": "n", "input": "str"}]}
    assert parse_response(odd).tool_call == ToolCall("t", "n", {})


def provider(handler, monkeypatch: pytest.MonkeyPatch, **kw) -> AnthropicProvider:
    monkeypatch.setenv("ANTHROPIC_API_KEY", KEY)
    client = httpx.Client(transport=httpx.MockTransport(handler))
    return AnthropicProvider("claude-test", client=client, sleep=lambda s: None, **kw)


def test_complete_uses_the_documented_endpoint_and_headers(monkeypatch) -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=REPLY)

    p = provider(handler, monkeypatch)
    out = p.complete([msg("system", "s"), msg("user", "hi")], [READ], {}, trial_index=0)
    assert out.text == "All done."
    req = seen[0]
    assert (req.method, str(req.url)) == ("POST", "https://api.anthropic.com/v1/messages")
    assert req.headers["x-api-key"] == KEY and req.headers["anthropic-version"] == "2023-06-01"
    assert req.headers["content-type"] == "application/json"
    sent = json.loads(req.content)
    assert sent["system"] == "s" and sent["tools"][0]["name"] == "read_file"


def test_a_429_then_success_is_retried_through_complete(monkeypatch) -> None:
    replies = iter([httpx.Response(429, json={"error": {"message": "slow"}}),
                    httpx.Response(200, json=REPLY)])
    p = provider(lambda r: next(replies), monkeypatch)
    assert p.complete([msg("user", "hi")], [], {}, 0).text == "All done."


def test_a_400_fails_at_once_without_retry(monkeypatch) -> None:
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(400, json={"error": {"message": "max_tokens: too large"}})

    with pytest.raises(ProviderError, match="too large"):
        provider(handler, monkeypatch).complete([msg("user", "hi")], [], {}, 0)
    assert len(calls) == 1


def test_a_missing_key_fails_before_any_request(monkeypatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    calls: list[int] = []
    transport = httpx.MockTransport(lambda r: calls.append(1) or httpx.Response(200))
    client = httpx.Client(transport=transport)
    with pytest.raises(MissingKey, match="ANTHROPIC_API_KEY"):
        AnthropicProvider("m", client=client).complete([msg("user", "hi")], [], {}, 0)
    assert calls == []


def test_the_key_is_not_stored_on_the_provider_or_shown_in_its_repr(monkeypatch) -> None:
    p = provider(lambda r: httpx.Response(200, json=REPLY), monkeypatch)
    p.complete([msg("user", "hi")], [], {}, 0)
    assert KEY not in repr(p) and KEY not in str(vars(p))


def test_the_key_never_reaches_the_response_the_loop_sees(monkeypatch) -> None:
    echo = {**REPLY, "content": [{"type": "text", "text": "ok"}]}
    out = provider(lambda r: httpx.Response(200, json=echo), monkeypatch).complete(
        [msg("user", "hi")], [], {}, 0)
    assert KEY not in repr(out)


def test_a_per_call_max_tokens_overrides_the_constructor_default(monkeypatch) -> None:
    sent: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        sent.append(json.loads(request.content)["max_tokens"])
        return httpx.Response(200, json=REPLY)

    p = provider(handler, monkeypatch)
    p.complete([msg("user", "hi")], [], {"max_tokens": 400}, 0)
    p.complete([msg("user", "hi")], [], {}, 0)
    assert sent == [400, 1024]  # the cap is honoured when given, the default otherwise
