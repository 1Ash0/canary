"""The loop against a scripted provider: stop conditions, pairing, errors, compaction, replay."""

from collections.abc import Sequence
from itertools import count as counter

import pytest

from ctxcheck.fates import derive_fates
from ctxcheck.harness.loop import Scenario, Turn, run
from ctxcheck.harness.tools import Tool
from ctxcheck.harness.types import Message, ModelResponse, ToolCall, ToolSpec
from ctxcheck.ledger import replay
from ctxcheck.policies.base import PolicyContext
from ctxcheck.providers.scripted import ScriptedProvider, ScriptExhausted
from ctxcheck.schema import TraceEvent, parse_event


def words(text: str) -> int:
    return len(text.split())


def clock():
    ticks = counter()
    return lambda: f"2026-10-20T00:00:{next(ticks):02d}Z"


READ = Tool(
    ToolSpec("read_file", "Read a file",
             {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}),
    fn=lambda path: f"contents of {path} " + "word " * 20,
)
POST = Tool(
    ToolSpec("post_status", "Post a status",
             {"type": "object",
              "properties": {"channel": {"type": "string"}, "text": {"type": "string"}},
              "required": ["channel", "text"]}),
    fn=lambda channel, text: f"posted to {channel}",
    terminal=True,
)
TOOLS = [READ, POST]


def say(text: str = "done") -> ModelResponse:
    return ModelResponse(text=text)


def call(tool: str, call_id: str = "c1", /, **args: object) -> ModelResponse:
    return ModelResponse(tool_call=ToolCall(call_id, tool, dict(args)))


def go(scenario: Scenario, replies: list[ModelResponse], **kw) -> list[TraceEvent]:
    kw.setdefault("limit_tokens", 10_000)
    return run(scenario, ScriptedProvider(replies), TOOLS, count_fn=words, clock=clock(), **kw)


def types(events: Sequence[TraceEvent]) -> list[str]:
    return [e.type for e in events]


def end(events: Sequence[TraceEvent]):
    last = events[-1]
    assert last.type == "run_end"
    return last


ONE = Scenario("s", "You are an agent.", [Turn("Please check the build.")])
TWO = Scenario("s", "You are an agent.", [Turn("First task."), Turn("Second task.")])


def test_ends_when_the_model_finishes_without_a_tool_call() -> None:
    events = go(ONE, [say()])
    assert types(events)[0] == "run_start"
    assert (end(events).status, end(events).reason) == ("ok", "end_turn")
    assert end(events).totals["model_calls"] == 1


def test_tool_call_then_result_then_the_model_continues() -> None:
    events = go(ONE, [call("read_file", path="a.py"), say()])
    assert types(events) == [
        "run_start", "message", "message", "model_call", "message", "tool_call", "tool_result",
        "message", "model_call", "message", "run_end",
    ]


def test_every_tool_call_is_paired_with_its_result() -> None:
    events = go(ONE, [call("read_file", "c1", path="a"), call("read_file", "c2", path="b"), say()])
    calls = [e.call_id for e in events if e.type == "tool_call"]
    results = [e.call_id for e in events if e.type == "tool_result"]
    assert calls == results == ["c1", "c2"]


def test_a_terminal_tool_ends_the_run_and_its_arguments_are_recorded() -> None:
    events = go(ONE, [call("post_status", channel="#ops-7", text="ok")])
    assert (end(events).status, end(events).reason) == ("ok", "terminal_tool")
    posted = next(e for e in events if e.type == "tool_call")
    assert posted.args == {"channel": "#ops-7", "text": "ok"}


def test_a_terminal_call_with_bad_arguments_does_not_end_the_run() -> None:
    events = go(ONE, [call("post_status", channel="#ops-7"), say()])  # missing `text`
    result = next(e for e in events if e.type == "tool_result")
    assert result.is_error and end(events).reason == "end_turn"


def test_unknown_tool_is_an_error_result_and_the_run_continues() -> None:
    events = go(ONE, [call("delete_branch", name="main"), say()])
    result = next(e for e in events if e.type == "tool_result")
    assert result.is_error and "unknown tool" in result.result
    assert end(events).reason == "end_turn"


def test_max_calls_per_turn_aborts_a_looping_model() -> None:
    replies = [call("read_file", f"c{i}", path="a") for i in range(10)]
    events = go(ONE, replies, max_calls_per_turn=3)
    assert (end(events).status, end(events).reason) == ("aborted", "max_calls")
    assert end(events).totals["model_calls"] == 3


def test_each_user_turn_is_its_own_step() -> None:
    events = go(TWO, [say("one"), say("two")])
    steps = [e.step for e in events if e.type == "message" and e.origin == "user"]
    assert steps == [1, 1, 2]  # the system message shares step 1
    assert end(events).totals["steps"] == 2


def test_the_provider_sees_the_growing_window_and_the_tools() -> None:
    provider = ScriptedProvider([say("one"), say("two")])
    run(TWO, provider, TOOLS, limit_tokens=10_000, count_fn=words, clock=clock(), trial_index=4)
    first, second = provider.requests
    assert len(first["messages"]) == 2 and len(second["messages"]) == 4
    assert [t.name for t in first["tools"]] == ["read_file", "post_status"]
    assert first["trial"] == second["trial"] == 4


def test_script_exhaustion_is_loud_not_silent() -> None:
    with pytest.raises(ScriptExhausted):
        go(ONE, [call("read_file", path="a")])


def test_a_planted_fact_must_appear_verbatim_in_its_message() -> None:
    with pytest.raises(ValueError, match="verbatim"):
        Turn("Use the usual channel.", canary=("C1", "constraint", "post to #ops-7"))


class DropOldest:
    """A throwaway test policy (the real policies are M3): drop oldest non-system, add a summary."""

    name = "drop_oldest"

    def apply(
        self, window: Sequence[Message], budget_tokens: int, ctx: PolicyContext
    ) -> list[Message]:
        system, rest = window[0], list(window[1:])
        kept = rest[len(rest) // 2:]
        text = "Summary: earlier work happened."
        summary = Message(ctx.new_id(), "user", text, "summary", ctx.count(text), ctx.step)
        return [system, summary, *kept]


def long_scenario() -> Scenario:
    rule = "never call delete_branch on main"
    turns = [Turn(f"Rule: {rule}.", origin="canary", canary=("C1", "constraint", rule))]
    turns += [Turn("filler " * 12) for _ in range(6)]
    return Scenario("s", "You are an agent.", turns)


def test_no_compaction_while_the_window_fits() -> None:
    events = go(long_scenario(), [say()] * 7, limit_tokens=10_000, policy=DropOldest())
    assert "compaction" not in types(events)


def test_compaction_fires_before_the_call_that_would_overflow() -> None:
    events = go(long_scenario(), [say()] * 7, limit_tokens=80, policy=DropOldest())
    assert "compaction" in types(events) and end(events).status == "ok"
    first_compaction = next(i for i, e in enumerate(events) if e.type == "compaction")
    assert events[first_compaction + 1].type == "message"  # the summary comes after the event
    assert events[first_compaction + 1].origin == "summary"
    assert events[first_compaction + 2].type == "model_call"  # ...and before the model is asked


def test_the_window_never_exceeds_the_limit_at_a_model_call() -> None:
    events = go(long_scenario(), [say()] * 7, limit_tokens=80, policy=DropOldest())
    ledger = replay(events)
    # rows close at the end of each step, after the reply; the check happens before each call
    assert max(c.tokens_after for c in ledger.compactions) <= 80


def test_without_a_policy_an_overflow_ends_the_run_cleanly() -> None:
    events = go(long_scenario(), [say()] * 7, limit_tokens=60, policy=None)
    assert (end(events).status, end(events).reason) == ("error", "budget_exceeded")


def test_a_policy_that_cannot_get_under_the_limit_ends_the_run_cleanly() -> None:
    events = go(long_scenario(), [say()] * 7, limit_tokens=5, policy=DropOldest())
    assert (end(events).status, end(events).reason) == ("error", "budget_exceeded")


def test_every_emitted_event_survives_a_json_round_trip() -> None:
    events = go(long_scenario(), [say()] * 7, limit_tokens=80, policy=DropOldest())
    assert [parse_event(e.model_dump_json()) for e in events] == events


def test_seq_is_dense_and_the_clock_is_used() -> None:
    events = go(TWO, [say(), say()])
    assert [e.seq for e in events] == list(range(len(events)))
    assert events[0].ts == "2026-10-20T00:00:00Z"


def test_replaying_the_run_reproduces_the_loops_own_final_token_count() -> None:
    events = go(long_scenario(), [say()] * 7, limit_tokens=80, policy=DropOldest())
    ledger = replay(events)
    assert ledger.rows[-1].total == end(events).totals["tokens_final"]


def test_the_planted_canary_is_recorded_and_its_fate_is_derived_from_the_run() -> None:
    kept = go(long_scenario(), [say()] * 7, limit_tokens=10_000, policy=DropOldest())
    assert derive_fates(kept) == {"C1": "kept"}
    gone = go(long_scenario(), [say()] * 7, limit_tokens=80, policy=DropOldest())
    assert derive_fates(gone) == {"C1": "gone"}
