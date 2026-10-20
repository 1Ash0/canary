"""Fate rule tests: each outcome must fire, and each near-miss must not."""

import pytest

from ctxcheck.fates import derive_fates
from ctxcheck.schema import (
    CanaryPlantedEvent,
    CompactionEvent,
    MessageEvent,
    RunStartEvent,
    TraceEvent,
)
from ctxcheck.synthetic import generate

TS = "2026-10-20T00:00:00Z"
RULE = "never call delete_branch on main"


def start() -> RunStartEvent:
    return RunStartEvent(
        type="run_start", run_id="r", seq=0, ts=TS, scenario_id="s", seed=1, policy="p",
        provider="p", model="m", limit_tokens=100, tools_tokens_est=0,
    )


def msg(seq: int, mid: str, text: str, origin="user") -> MessageEvent:
    return MessageEvent(
        type="message", run_id="r", seq=seq, ts=TS, message_id=mid, step=1, role="user",
        content=text, tokens_est=1, origin=origin,
    )


def planted(seq: int, mid: str = "c1") -> CanaryPlantedEvent:
    return CanaryPlantedEvent(
        type="canary_planted", run_id="r", seq=seq, ts=TS, canary_id="C1", canary_type="constraint",
        message_id=mid, value=RULE,
    )


def drop(seq: int, ids: list[str]) -> CompactionEvent:
    return CompactionEvent(
        type="compaction", run_id="r", seq=seq, ts=TS, policy="p", trigger="budget",
        tokens_before=0, tokens_after=0, kept_ids=[], dropped_ids=ids, added_ids=[],
    )


def base() -> list[TraceEvent]:
    return [start(), msg(1, "c1", f"Rule: {RULE}.", origin="canary"), planted(2)]


def test_no_compaction_means_kept() -> None:
    assert derive_fates(base()) == {"C1": "kept"}


def test_dropped_and_not_in_summary_is_gone() -> None:
    summary = msg(4, "s1", "Summary: nothing relevant.", origin="summary")
    events = [*base(), drop(3, ["c1"]), summary]
    assert derive_fates(events) == {"C1": "gone"}


def test_verbatim_in_summary_is_kept() -> None:
    events = [*base(), drop(3, ["c1"]), msg(4, "s1", f"Summary. {RULE}.", origin="summary")]
    assert derive_fates(events) == {"C1": "kept"}


def test_paraphrase_is_gone_not_changed() -> None:
    summary = msg(4, "s1", "Summary: do not delete main.", origin="summary")
    events = [*base(), drop(3, ["c1"]), summary]
    assert derive_fates(events) == {"C1": "gone"}


def test_case_difference_is_gone() -> None:
    events = [*base(), drop(3, ["c1"]), msg(4, "s1", RULE.upper(), origin="summary")]
    assert derive_fates(events) == {"C1": "gone"}


def test_message_not_dropped_stays_kept() -> None:
    events = [*base(), msg(3, "x", "filler"), drop(4, ["x"])]
    assert derive_fates(events) == {"C1": "kept"}


def test_fact_dropped_then_reintroduced_by_a_later_summary_is_kept() -> None:
    events = [*base(), drop(3, ["c1"]), msg(4, "s1", f"Again: {RULE}", origin="summary")]
    assert derive_fates(events)["C1"] == "kept"


def test_dropping_an_unknown_message_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown message"):
        derive_fates([*base(), drop(3, ["ghost"])])


def test_trace_must_begin_with_run_start() -> None:
    with pytest.raises(ValueError, match="run_start"):
        derive_fates([msg(0, "c1", "x")])


def test_fixture_fates_are_one_kept_two_gone() -> None:
    fates = derive_fates(generate(1, count_fn=lambda t: len(t.split())))
    assert fates == {"C1": "kept", "C2": "gone", "C3": "gone"}
