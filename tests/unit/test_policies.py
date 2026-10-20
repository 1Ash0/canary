"""The four policies, one behaviour at a time, then through the loop."""

from collections.abc import Sequence
from itertools import count as counter

import pytest

from ctxcheck.fates import derive_fates
from ctxcheck.harness.loop import Scenario, Turn, run
from ctxcheck.harness.tools import Tool
from ctxcheck.harness.types import Message, ModelResponse, ToolCall, ToolSpec
from ctxcheck.policies import (
    DETERMINISTIC,
    PROMPTS,
    HeadTail,
    IrreducibleBudget,
    LLMSummary,
    ObservationMask,
    PolicyContext,
    RecencyTruncate,
    SummaryFailed,
    make_policy,
    summary_looks_valid,
)
from ctxcheck.providers._http import ProviderError
from ctxcheck.providers.scripted import ScriptedProvider
from ctxcheck.schema import TraceEvent


def words(text: str) -> int:
    return len(text.split())


def ctx(provider=None, record=None, trial=0) -> PolicyContext:
    ids = counter(900)
    return PolicyContext(step=3, new_id=lambda: f"n{next(ids)}", count=words, trial_index=trial,
                         provider=provider, record_call=record)


def msg(i: int, role: str, n: int, **kw) -> Message:
    origin = {"system": "user", "tool": "tool", "assistant": "assistant"}.get(role, role)
    return Message(f"m{i:03d}", role, f"{role} {i} " + "w " * n, origin, n, 1, **kw)  # type: ignore[arg-type]


def window() -> list[Message]:
    """system(10) | user(10) asst(10) | call(5)+result(40) | user(10) asst(10) | user(10) [tail]"""
    call = ToolCall("c1", "read_file", {"path": "a"})
    return [
        msg(0, "system", 10),
        msg(1, "user", 10), msg(2, "assistant", 10),
        msg(3, "assistant", 5, call_id="c1", tool_call=call), msg(4, "tool", 40, call_id="c1"),
        msg(5, "user", 10), msg(6, "assistant", 10),
        msg(7, "user", 10),
    ]


def ids(w: Sequence[Message]) -> list[str]:
    return [m.id for m in w]


# --- shared behaviour ---------------------------------------------------------------------------

@pytest.mark.parametrize("name", DETERMINISTIC)
def test_a_window_under_budget_is_returned_unchanged(name: str) -> None:
    w = window()
    assert make_policy(name).apply(w, 1000, ctx()) == w


@pytest.mark.parametrize("name", DETERMINISTIC)
def test_system_and_current_turn_are_never_dropped(name: str) -> None:
    w = window()
    out = make_policy(name).apply(w, 60, ctx())
    assert out[0].id == "m000" and out[-1].id == "m007"


@pytest.mark.parametrize("name", DETERMINISTIC)
def test_irreducible_budget_raises_instead_of_overrunning(name: str) -> None:
    with pytest.raises(IrreducibleBudget, match="no policy can drop them"):
        make_policy(name).apply(window(), 15, ctx())  # system 10 + tail 10 = 20 > 15


def test_unknown_policy_names_the_known_ones() -> None:
    with pytest.raises(ValueError, match="head_tail"):
        make_policy("nope")


# --- recency_truncate ---------------------------------------------------------------------------

def test_recency_drops_the_oldest_first_and_stops_at_the_target() -> None:
    out = RecencyTruncate(target_ratio=1.0).apply(window(), 80, ctx())
    # total 105 > 80: drop m001 m002 (20) -> 85, still > 80: drop the tool unit (45) -> 40
    assert ids(out) == ["m000", "m005", "m006", "m007"]


def test_recency_never_splits_a_tool_call_from_its_result() -> None:
    out = RecencyTruncate(target_ratio=1.0).apply(window(), 100, ctx())  # drops m001 m002 only
    assert "m003" in ids(out) and "m004" in ids(out)
    out = RecencyTruncate(target_ratio=1.0).apply(window(), 85, ctx())
    assert ("m003" in ids(out)) == ("m004" in ids(out))


def test_recency_compacts_below_the_limit_not_to_it() -> None:
    out = RecencyTruncate(target_ratio=0.5).apply(window(), 100, ctx())
    assert sum(m.tokens_est for m in out) <= 50


# --- head_tail ----------------------------------------------------------------------------------

def test_head_tail_keeps_the_start_and_the_newest_and_drops_the_middle() -> None:
    out = HeadTail(target_ratio=1.0, head_ratio=0.5).apply(window(), 70, ctx())
    # room = 70 - 20 = 50; head room 25: m001 m002 (20); tail: m006+m005 (20) fits, tool unit no
    assert ids(out) == ["m000", "m001", "m002", "m005", "m006", "m007"]


def test_head_tail_with_no_head_is_recency() -> None:
    a = HeadTail(target_ratio=1.0, head_ratio=0.0).apply(window(), 80, ctx())
    b = RecencyTruncate(target_ratio=1.0).apply(window(), 80, ctx())
    assert ids(a) == ids(b)


def test_head_tail_keeps_a_contiguous_head_never_a_gap() -> None:
    out = HeadTail(target_ratio=1.0, head_ratio=0.2).apply(window(), 70, ctx())
    kept = ids(out)
    assert "m001" in kept and "m002" not in kept or "m002" in kept  # head is a prefix of history
    hist = [i for i in kept if i not in ("m000", "m007")]
    assert hist == sorted(hist)


# --- observation_mask ---------------------------------------------------------------------------

def test_mask_replaces_an_old_tool_output_and_keeps_everything_else() -> None:
    out = ObservationMask(target_ratio=1.0, keep_recent=0).apply(window(), 80, ctx())
    assert ids(out)[:4] == ["m000", "m001", "m002", "m003"]  # call kept
    masked = out[4]
    assert masked.id == "n900" and masked.role == "tool" and masked.call_id == "c1"
    assert masked.origin == "tool" and "omitted: 40 tokens" in masked.content
    assert masked.tokens_est == 5 and "m004" not in ids(out)


def test_mask_leaves_the_newest_outputs_alone() -> None:
    out = ObservationMask(target_ratio=1.0, keep_recent=1).apply(window(), 80, ctx())
    # the only tool output counts as recent, so it is never masked; the fallback drops it whole
    assert not any("omitted" in m.content for m in out)
    assert sum(m.tokens_est for m in out) <= 80


def test_mask_falls_back_to_dropping_when_masking_is_not_enough() -> None:
    out = ObservationMask(target_ratio=1.0, keep_recent=0).apply(window(), 50, ctx())
    assert sum(m.tokens_est for m in out) <= 50 and out[0].id == "m000" and out[-1].id == "m007"


def test_mask_skips_outputs_too_small_to_be_worth_masking() -> None:
    w = window()
    w[4] = msg(4, "tool", 3, call_id="c1")  # placeholder is 5 words: masking would grow it
    out = ObservationMask(target_ratio=1.0, keep_recent=0).apply(w, 50, ctx())
    assert not any("omitted" in m.content for m in out)


# --- llm_summary --------------------------------------------------------------------------------

def reply(text: str = "The user wants X. Rule: use #ops-7.") -> ModelResponse:
    return ModelResponse(text=text, input_tokens=50, output_tokens=12, model_id="m-1")


def test_summary_replaces_old_units_and_sits_right_after_the_system_prompt() -> None:
    provider = ScriptedProvider([reply()])
    out = LLMSummary(keep_units=2).apply(window(), 80, ctx(provider))
    assert out[0].id == "m000"
    assert out[1].origin == "summary" and out[1].role == "user"
    assert out[1].content.startswith("[Summary of earlier conversation]")
    assert ids(out)[2:] == ["m005", "m006", "m007"]  # recent units and the tail untouched


def test_summary_request_is_the_versioned_prompt_plus_the_dropped_text_with_no_tools() -> None:
    provider = ScriptedProvider([reply()])
    LLMSummary(prompt_version="v1", keep_units=2).apply(window(), 80, ctx(provider, trial=3))
    sent = provider.requests[0]
    assert sent["tools"] == [] and sent["trial"] == 3
    system, body = sent["messages"]
    assert system.content == PROMPTS["v1"] and system.role == "system"
    assert "user 1" in body.content and "tool 4" in body.content  # the old text is included
    assert "user 7" not in body.content  # the current turn is not summarised


def test_prompt_versions_differ_and_unknown_versions_are_rejected() -> None:
    assert PROMPTS["v1"] != PROMPTS["v2"]
    assert "instruction" not in PROMPTS["v1"]  # v1 is the generic baseline
    with pytest.raises(ValueError, match="unknown prompt version"):
        LLMSummary(prompt_version="v9")


def test_summary_calls_are_reported_so_the_loop_can_log_them() -> None:
    seen: list[ModelResponse] = []
    LLMSummary(keep_units=2).apply(window(), 80,
                                   ctx(ScriptedProvider([reply()]), lambda r, m: seen.append(r)))
    assert len(seen) == 1 and seen[0].input_tokens == 50


def test_empty_summary_fails_loudly() -> None:
    with pytest.raises(SummaryFailed, match="no text"):
        LLMSummary(keep_units=2).apply(window(), 80, ctx(ScriptedProvider([reply("  ")])))


class Raises:
    def __init__(self, error: Exception) -> None:
        self.error = error

    def complete(self, *args, **kwargs):
        raise self.error


def test_a_rejected_summary_request_is_a_summary_failure_not_a_crash() -> None:
    rejected = ProviderError("400: Tool choice is none, but model called a tool", 400)
    with pytest.raises(SummaryFailed, match="rejected"):
        LLMSummary(keep_units=2).apply(window(), 80, ctx(Raises(rejected)))


def test_rate_limits_and_server_errors_are_not_blamed_on_the_summarizer() -> None:
    for error in (ProviderError("429: slow down", 429), ProviderError("500: oops", 500),
                  ProviderError("gave up after 4 attempts; last: 429")):
        with pytest.raises(ProviderError):
            LLMSummary(keep_units=2).apply(window(), 80, ctx(Raises(error)))


def test_summary_needs_a_provider() -> None:
    with pytest.raises(SummaryFailed, match="provider"):
        LLMSummary().apply(window(), 80, ctx(None))


def test_nothing_to_summarise_leaves_the_window_alone() -> None:
    provider = ScriptedProvider([])
    out = LLMSummary(keep_units=10).apply(window(), 80, ctx(provider))
    assert out == window() and provider.requests == []


# --- through the loop ---------------------------------------------------------------------------

RULE = "never post to #general"
READ = Tool(ToolSpec("read_file", "Read",
                     {"type": "object", "properties": {"path": {"type": "string"}},
                      "required": ["path"]}), fn=lambda path: "contents " + "w " * 15)


def scenario() -> Scenario:
    turns = [Turn(f"Rule: {RULE}.", origin="canary", canary=("C1", "constraint", RULE))]
    turns += [Turn("filler " * 12) for _ in range(5)]
    return Scenario("s", "You are an agent.", turns)


def clock():
    ticks = counter()
    return lambda: f"2026-10-20T00:00:{next(ticks):02d}Z"


def go(policy, replies, limit=70) -> list[TraceEvent]:
    return run(scenario(), ScriptedProvider(replies), [READ], limit_tokens=limit, policy=policy,
               count_fn=words, clock=clock())


def end(events):
    last = events[-1]
    assert last.type == "run_end"
    return last


def test_every_deterministic_policy_compacts_through_the_loop_and_the_run_finishes() -> None:
    for name in DETERMINISTIC:
        events = go(make_policy(name), [ModelResponse(text="ok")] * 6)
        assert any(e.type == "compaction" and e.policy == name for e in events), name
        assert end(events).status == "ok", name


def test_recency_loses_the_early_canary_and_head_tail_keeps_it() -> None:
    lost = derive_fates(go(RecencyTruncate(), [ModelResponse(text="ok")] * 6))
    kept = derive_fates(go(HeadTail(head_ratio=0.5), [ModelResponse(text="ok")] * 6))
    assert lost == {"C1": "gone"} and kept == {"C1": "kept"}


def test_the_loop_ends_with_irreducible_budget_as_the_reason() -> None:
    events = go(RecencyTruncate(), [ModelResponse(text="ok")] * 6, limit=12)
    assert (end(events).status, end(events).reason) == ("error", "irreducible_budget")


def test_llm_summary_through_the_loop_logs_the_call_the_prompt_version_and_the_fate() -> None:
    # replies are consumed in call order: agent turns 1-4, then the summary (the window first
    # overflows before turn 5), then the rest
    replies = [*[ModelResponse(text="ok")] * 4, ModelResponse(text=f"Summary. Rule: {RULE}."),
               *[ModelResponse(text="ok")] * 4]
    events = go(LLMSummary(prompt_version="v1", keep_units=1), replies, limit=70)
    compaction = next(e for e in events if e.type == "compaction")
    assert compaction.policy == "llm_summary" and compaction.prompt_version == "v1"
    assert compaction.summary_message_id is not None
    assert end(events).totals["summary_calls"] >= 1
    calls_before = [e for e in events if e.type == "model_call"]
    assert len(calls_before) == end(events).totals["model_calls"] + end(events).totals[
        "summary_calls"]
    assert derive_fates(events)["C1"] == "kept"  # this summary quoted the rule verbatim


def test_a_summary_that_drops_the_rule_makes_it_gone() -> None:
    replies = [*[ModelResponse(text="ok")] * 4,
               ModelResponse(text="Summary. The user asked for some work."),
               *[ModelResponse(text="ok")] * 4]
    events = go(LLMSummary(keep_units=1), replies, limit=70)
    assert derive_fates(events)["C1"] == "gone"


# --- is a summary a summary? ---------------------------------------------------------------------

DROPPED = [
    "Standing rule for this project: every status update must be posted to #relay-47.",
    "Please check what changed in notes.md and tell me anything odd.",
    "12:35:10 indexer.flushed 372 rows in 220ms\n20:01:21 cache.retried 356 batches in 129ms",
    "I read notes.md. indexer processed 106 records; nothing looks wrong.",
]


def test_a_real_summary_is_valid_even_when_it_quotes_the_rule() -> None:
    text = ("[Summary of earlier conversation]\nThe user asked for several files to be reviewed "
            "and nothing was wrong.\nStanding rule: every status update must be posted to "
            "#relay-47.")
    assert summary_looks_valid(text, DROPPED)


def test_a_short_wrong_summary_is_still_valid_it_is_a_flag_not_a_quality_grade() -> None:
    assert summary_looks_valid("[Summary of earlier conversation]\nThe user reviewed files.",
                               DROPPED)


def test_echoing_a_transcript_line_is_not_a_summary() -> None:
    for echoed in (
        '[tool_call read_file {"path": "notes.md"}]',
        '[assistant] [tool_call read_file {"path": "notes.md"}]\n[tool] 12:35:10 indexer.flushed',
        "I read notes.md. indexer processed 106 records; nothing looks wrong.",
        "12:35:10 indexer.flushed 372 rows in 220ms\n20:01:21 cache.retried 356 batches in 129ms",
    ):
        assert not summary_looks_valid(f"[Summary of earlier conversation]\n{echoed}", DROPPED)


def test_an_empty_summary_is_not_valid() -> None:
    assert not summary_looks_valid("[Summary of earlier conversation]\n  ", DROPPED)
