"""The real adapters driven by the real loop over a fake transport: the integration the unit tests
do not cover. Each adapter receives the loop's actual messages and its replies steer the loop."""

import json
from itertools import count as counter

import httpx
import pytest

from ctxcheck.harness.loop import Scenario, Turn, run
from ctxcheck.harness.tools import Tool
from ctxcheck.harness.types import ToolSpec
from ctxcheck.ledger import replay
from ctxcheck.providers.anthropic import AnthropicProvider
from ctxcheck.providers.openai_compat import OpenAICompatProvider

READ_SCHEMA = {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}
POST_SCHEMA = {
    "type": "object", "properties": {"channel": {"type": "string"}}, "required": ["channel"],
}
READ = Tool(ToolSpec("read_file", "Read a file", READ_SCHEMA), fn=lambda path: f"text of {path}")
POST_SPEC = ToolSpec("post_status", "Post", POST_SCHEMA)
POST = Tool(POST_SPEC, fn=lambda channel: "posted", terminal=True)
SCENARIO = Scenario("s", "You are an agent.", [Turn("Check the build, then post a status.")])


def words(text: str) -> int:
    return len(text.split())


def clock():
    ticks = counter()
    return lambda: f"2026-10-20T00:00:{next(ticks):02d}Z"


def tool_use(call_id: str, name: str, args: dict) -> dict:
    return {"type": "tool_use", "id": call_id, "name": name, "input": args}


def function_call(call_id: str, name: str, args: dict) -> dict:
    fn = {"name": name, "arguments": json.dumps(args)}
    call = {"id": call_id, "type": "function", "function": fn}
    return {"role": "assistant", "content": None, "tool_calls": [call]}


def anthropic_replies() -> list[dict]:
    usage = {"input_tokens": 50, "output_tokens": 9, "cache_read_input_tokens": 40}
    first = [{"type": "text", "text": "Reading."}, tool_use("t1", "read_file", {"path": "a"})]
    second = [tool_use("t2", "post_status", {"channel": "#ops-7"})]
    return [{"model": "claude-x", "content": c, "usage": usage} for c in (first, second)]


def openai_replies() -> list[dict]:
    usage = {"prompt_tokens": 50, "completion_tokens": 9}
    msgs = [function_call("c1", "read_file", {"path": "a"}),
            function_call("c2", "post_status", {"channel": "#ops-7"})]
    return [{"model": "gpt-x", "choices": [{"message": m}], "usage": usage} for m in msgs]


def make(kind: str, monkeypatch: pytest.MonkeyPatch):
    sent: list[dict] = []
    replies = iter(anthropic_replies() if kind == "anthropic" else openai_replies())

    def handler(request: httpx.Request) -> httpx.Response:
        sent.append(json.loads(request.content))
        return httpx.Response(200, json=next(replies))

    client = httpx.Client(transport=httpx.MockTransport(handler))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-1234567890")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-oai-test-1234567890")
    cls = AnthropicProvider if kind == "anthropic" else OpenAICompatProvider
    return cls("m", client=client, sleep=lambda s: None), sent


def go(provider):
    return run(SCENARIO, provider, [READ, POST], limit_tokens=10_000, count_fn=words, clock=clock())


@pytest.mark.parametrize("kind", ["anthropic", "openai"])
def test_a_two_call_task_runs_through_the_adapter_to_a_terminal_tool(kind, monkeypatch) -> None:
    provider, sent = make(kind, monkeypatch)
    events = go(provider)
    end = events[-1]
    assert (end.status, end.reason, end.totals["model_calls"]) == ("ok", "terminal_tool", 2)
    graded = [e for e in events if e.type == "tool_call"][-1]
    assert graded.name == "post_status" and graded.args == {"channel": "#ops-7"}
    assert len(sent) == 2


@pytest.mark.parametrize("kind", ["anthropic", "openai"])
def test_the_second_request_carries_the_first_calls_structured_history(kind, monkeypatch) -> None:
    provider, sent = make(kind, monkeypatch)
    go(provider)
    second = json.dumps(sent[1]["messages"])
    assert "text of a" in second  # the tool result came back
    if kind == "anthropic":
        assert '"tool_use"' in second and '"tool_result"' in second and "t1" in second
    else:
        assert '"tool_calls"' in second and '"role": "tool"' in second and "c1" in second


def test_anthropic_cache_usage_flows_from_the_adapter_into_the_trace(monkeypatch) -> None:
    provider, _ = make("anthropic", monkeypatch)
    call = next(e for e in go(provider) if e.type == "model_call")
    assert call.cache_read_input_tokens == 40 and call.model_id_reported == "claude-x"
    assert call.input_tokens == 50


def test_openai_leaves_cache_fields_unreported(monkeypatch) -> None:
    provider, _ = make("openai", monkeypatch)
    call = next(e for e in go(provider) if e.type == "model_call")
    assert call.cache_read_input_tokens is None and call.model_id_reported == "gpt-x"


@pytest.mark.parametrize("kind", ["anthropic", "openai"])
def test_the_trace_replays_cleanly_and_never_contains_a_key(kind, monkeypatch) -> None:
    provider, _ = make(kind, monkeypatch)
    events = go(provider)
    assert replay(events).rows
    blob = "".join(e.model_dump_json() for e in events)
    assert "sk-ant-test" not in blob and "sk-oai-test" not in blob
