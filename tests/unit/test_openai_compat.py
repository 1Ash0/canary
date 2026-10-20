"""OpenAI-compatible adapter against fake replies shaped like the documented ones. No network."""

import json

import httpx
import pytest

from ctxcheck.harness.tools import Tool, dispatch
from ctxcheck.harness.types import BAD_ARGS_KEY, Message, ToolCall, ToolSpec
from ctxcheck.providers._http import MissingKey, ProviderError
from ctxcheck.providers.openai_compat import OpenAICompatProvider, build_request, parse_response

KEY = "sk-test-SECRET-OPENAI-1234567890"
SCHEMA = {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}
READ = ToolSpec("read_file", "Read a file", SCHEMA)
_ids = iter(range(10_000))


def msg(role, content="", *, origin=None, **kw) -> Message:
    return Message(f"m{next(_ids)}", role, content, origin or role, 1, 1, **kw)


def build(messages, tools=(), params=None, field="max_tokens"):
    return build_request("gpt-test", 256, field, messages, tools, params or {})


def test_system_prompt_stays_a_system_message() -> None:
    body = build([msg("system", "Be brief."), msg("user", "hi")])
    assert body["messages"] == [{"role": "system", "content": "Be brief."},
                                {"role": "user", "content": "hi"}]
    assert body["model"] == "gpt-test" and body["max_tokens"] == 256


def test_the_max_tokens_field_name_is_configurable() -> None:
    body = build([msg("user", "hi")], field="max_completion_tokens")
    assert body["max_completion_tokens"] == 256 and "max_tokens" not in body


def test_tools_are_function_tools_and_parallel_calls_are_off() -> None:
    body = build([msg("user", "hi")], tools=[READ])
    assert body["tools"] == [{"type": "function", "function": {
        "name": "read_file", "description": "Read a file", "parameters": SCHEMA}}]
    assert body["parallel_tool_calls"] is False


def test_no_tools_means_no_parallel_flag() -> None:
    assert "parallel_tool_calls" not in build([msg("user", "hi")])


def test_temperature_only_when_asked() -> None:
    assert "temperature" not in build([msg("user", "hi")])
    assert build([msg("user", "hi")], params={"temperature": 0.2})["temperature"] == 0.2


def test_a_tool_round_trip_uses_string_arguments_then_a_tool_message() -> None:
    call = ToolCall("call_1", "read_file", {"path": "a.py"})
    out = build([
        msg("user", "check"),
        msg("assistant", "[tool_call]", call_id="call_1", tool_call=call, lead_in="checking"),
        msg("tool", "file text", call_id="call_1"),
    ])["messages"]
    assistant = out[1]
    assert assistant["content"] == "checking"
    fn = assistant["tool_calls"][0]["function"]
    assert assistant["tool_calls"][0]["id"] == "call_1" and fn["name"] == "read_file"
    assert isinstance(fn["arguments"], str) and json.loads(fn["arguments"]) == {"path": "a.py"}
    assert out[2] == {"role": "tool", "tool_call_id": "call_1", "content": "file text"}


def test_a_tool_call_without_lead_in_sends_null_content() -> None:
    call = ToolCall("c", "read_file", {})
    out = build([msg("assistant", "[x]", call_id="c", tool_call=call)])["messages"][0]
    assert out["content"] is None


def test_empty_messages_are_dropped() -> None:
    assert [m["content"] for m in build([msg("user", ""), msg("user", "hi")])["messages"]] == ["hi"]


def reply(message: dict, usage: dict | None = None, finish: str = "stop") -> dict:
    return {"id": "x", "model": "gpt-test-1", "choices": [{"index": 0, "message": message,
            "finish_reason": finish}],
            "usage": usage or {"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120}}


def tool_message(*calls: tuple[str, str, str]) -> dict:
    return {"role": "assistant", "content": None, "tool_calls": [
        {"id": i, "type": "function", "function": {"name": n, "arguments": a}}
        for i, n, a in calls]}


def test_parse_a_text_reply_and_usage() -> None:
    r = parse_response(reply({"role": "assistant", "content": "All done."}))
    assert (r.text, r.tool_call, r.model_id) == ("All done.", None, "gpt-test-1")
    assert (r.input_tokens, r.output_tokens) == (100, 20)
    assert r.cache_read_input_tokens is None and r.cache_creation_input_tokens is None


def test_parse_a_tool_call_decodes_the_json_string_arguments() -> None:
    r = parse_response(reply(tool_message(("call_9", "read_file", '{"path": "b.py"}')),
                             finish="tool_calls"))
    assert r.tool_call == ToolCall("call_9", "read_file", {"path": "b.py"})
    assert r.text == ""  # content was null


def test_two_tool_calls_take_the_first_and_record_the_rest() -> None:
    r = parse_response(reply(tool_message(("a", "read_file", "{}"), ("b", "read_file", "{}"))))
    assert r.tool_call.id == "a" and r.extra["dropped_tool_calls"] == 1  # type: ignore[union-attr]


@pytest.mark.parametrize("raw", ['{"path": ', "not json", "[1, 2]", '"str"'])
def test_malformed_arguments_become_a_recognisable_error_not_a_crash(raw: str) -> None:
    r = parse_response(reply(tool_message(("c", "read_file", raw))))
    assert r.tool_call is not None and BAD_ARGS_KEY in r.tool_call.args
    tool = Tool(READ, fn=lambda path: "x")
    result, _ = dispatch([tool], r.tool_call)  # the model is told, and the run continues
    assert result.is_error and "not valid JSON" in result.text and "missing" not in result.text


def test_empty_arguments_are_an_empty_object() -> None:
    r = parse_response(reply(tool_message(("c", "ping", ""))))
    assert r.tool_call == ToolCall("c", "ping", {})


@pytest.mark.parametrize("data", [{}, {"choices": []}, {"choices": ["x"]}])
def test_a_reply_without_usable_choices_is_a_provider_error(data: dict) -> None:
    with pytest.raises(ProviderError):
        parse_response(data)


def test_missing_usage_is_zero_tokens_not_a_crash() -> None:
    data = reply({"role": "assistant", "content": "hi"})
    data.pop("usage")
    r = parse_response(data)
    assert (r.input_tokens, r.output_tokens) == (0, 0)


def provider(handler, monkeypatch: pytest.MonkeyPatch, **kw) -> OpenAICompatProvider:
    monkeypatch.setenv("OPENAI_API_KEY", KEY)
    client = httpx.Client(transport=httpx.MockTransport(handler))
    return OpenAICompatProvider("gpt-test", client=client, sleep=lambda s: None, **kw)


def test_complete_posts_to_chat_completions_with_a_bearer_header(monkeypatch) -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=reply({"role": "assistant", "content": "ok"}))

    out = provider(handler, monkeypatch).complete([msg("user", "hi")], [READ], {}, 0)
    assert out.text == "ok"
    req = seen[0]
    assert (req.method, str(req.url)) == ("POST", "https://api.openai.com/v1/chat/completions")
    assert req.headers["authorization"] == f"Bearer {KEY}"
    assert json.loads(req.content)["tools"][0]["function"]["name"] == "read_file"


def test_a_custom_base_url_for_a_local_or_hosted_compatible_server(monkeypatch) -> None:
    seen: list[httpx.Request] = []
    monkeypatch.setenv("LOCAL_KEY", "local-secret-key-1234")
    client = httpx.Client(transport=httpx.MockTransport(
        lambda r: seen.append(r) or httpx.Response(200, json=reply({"content": "ok"}))))
    p = OpenAICompatProvider("m", base_url="http://localhost:8000/v1/", api_key_env="LOCAL_KEY",
                             client=client)
    p.complete([msg("user", "hi")], [], {}, 0)
    assert str(seen[0].url) == "http://localhost:8000/v1/chat/completions"


def test_rate_limits_are_retried_and_client_errors_are_not(monkeypatch) -> None:
    replies = iter([httpx.Response(429, json={"error": {"message": "slow"}}),
                    httpx.Response(200, json=reply({"content": "ok"}))])
    assert provider(lambda r: next(replies), monkeypatch).complete(
        [msg("user", "hi")], [], {}, 0).text == "ok"

    calls: list[int] = []

    def bad(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(400, json={"error": {"message": "bad param"}})

    with pytest.raises(ProviderError, match="bad param"):
        provider(bad, monkeypatch).complete([msg("user", "hi")], [], {}, 0)
    assert len(calls) == 1


def test_a_missing_key_fails_before_any_request(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    calls: list[int] = []
    transport = httpx.MockTransport(lambda r: calls.append(1) or httpx.Response(200))
    with pytest.raises(MissingKey, match="OPENAI_API_KEY"):
        OpenAICompatProvider("m", client=httpx.Client(transport=transport)).complete(
            [msg("user", "hi")], [], {}, 0)
    assert calls == []


def test_the_key_is_not_stored_shown_or_leaked_through_an_echoing_error(monkeypatch) -> None:
    p = provider(lambda r: httpx.Response(401, json={"error": {"message": f"bad key {KEY}"}}),
                 monkeypatch)
    with pytest.raises(ProviderError) as exc:
        p.complete([msg("user", "hi")], [], {}, 0)
    assert KEY not in str(exc.value) and KEY not in repr(p) and KEY not in str(vars(p))


def test_the_parallel_flag_can_be_turned_off_for_servers_that_reject_it() -> None:
    tools = [READ]
    on = build_request("m", 1, "max_tokens", [msg("user", "hi")], tools, {})
    off = build_request("m", 1, "max_tokens", [msg("user", "hi")], tools, {}, False)
    assert on["parallel_tool_calls"] is False and "parallel_tool_calls" not in off


def test_the_provider_passes_the_option_through(monkeypatch) -> None:
    seen: list[dict] = []
    monkeypatch.setenv("OPENAI_API_KEY", KEY)

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(json.loads(request.content))
        return httpx.Response(200, json=reply({"content": "ok"}))

    client = httpx.Client(transport=httpx.MockTransport(handler))
    OpenAICompatProvider("m", client=client, limit_to_one_tool_call=False).complete(
        [msg("user", "hi")], [READ], {}, 0)
    assert "parallel_tool_calls" not in seen[0]


def test_a_per_call_max_tokens_overrides_the_constructor_default(monkeypatch) -> None:
    sent: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        sent.append(json.loads(request.content)["max_tokens"])
        return httpx.Response(200, json=reply({"role": "assistant", "content": "ok"}))

    p = provider(handler, monkeypatch)
    p.complete([msg("user", "hi")], [], {"max_tokens": 400}, 0)
    p.complete([msg("user", "hi")], [], {}, 0)
    assert sent == [400, 1024]  # the cap is honoured when given, the default otherwise
