"""The generator must be deterministic, internally consistent, and shaped as documented."""

import json
from pathlib import Path

from ctxcheck.ledger import replay
from ctxcheck.schema import (
    CanaryPlantedEvent,
    CompactionEvent,
    MessageEvent,
    RunStartEvent,
    parse_event,
)
from ctxcheck.synthetic import CANARIES, generate, write_jsonl


def words(text: str) -> int:  # offline stand-in for the real tokenizer
    return len(text.split())


def trace(seed: int = 1):
    return generate(seed, count_fn=words)


def test_same_seed_same_trace_different_seed_different_trace() -> None:
    assert trace(1) == trace(1)
    assert trace(1) != trace(2)


def test_seq_is_dense_and_timestamps_increase() -> None:
    events = trace()
    assert [e.seq for e in events] == list(range(len(events)))
    stamps = [e.ts for e in events]
    assert stamps == sorted(stamps) and len(set(stamps)) == len(stamps)


def test_starts_with_run_start_and_ends_with_run_end() -> None:
    events = trace()
    assert isinstance(events[0], RunStartEvent) and events[-1].type == "run_end"


def test_has_forty_steps_and_one_compaction_after_step_31() -> None:
    ledger = replay(trace())
    assert [r.step for r in ledger.rows] == list(range(1, 41))
    assert [c.after_step for c in ledger.compactions] == [31]


def test_window_stays_under_the_limit_and_compaction_shrinks_it() -> None:
    ledger = replay(trace())
    assert all(r.total < ledger.limit_tokens for r in ledger.rows)
    assert ledger.rows[31].total < ledger.rows[30].total


def test_compaction_event_matches_the_ledger() -> None:
    events = trace()
    ledger = replay(events)
    compaction = next(e for e in events if isinstance(e, CompactionEvent))
    assert compaction.tokens_before == ledger.rows[30].total
    assert compaction.tokens_after == ledger.rows[31].total - _step32_new_messages(events)


def _step32_new_messages(events) -> int:
    summary_id = next(e for e in events if isinstance(e, CompactionEvent)).summary_message_id
    return sum(
        e.tokens_est for e in events
        if isinstance(e, MessageEvent) and e.step == 32 and e.message_id != summary_id
    )


def test_three_canaries_planted_at_the_documented_steps() -> None:
    events = trace()
    planted = [e for e in events if isinstance(e, CanaryPlantedEvent)]
    assert [(p.canary_id, p.value) for p in planted] == [(c[0], c[3]) for c in CANARIES]
    by_id = {e.message_id: e for e in events if isinstance(e, MessageEvent)}
    assert [by_id[p.message_id].step for p in planted] == [c[2] for c in CANARIES]
    assert all(by_id[p.message_id].origin == "canary" for p in planted)


def test_summary_keeps_c1_verbatim_paraphrases_c2_and_omits_c3() -> None:
    events = trace()
    compaction = next(e for e in events if isinstance(e, CompactionEvent))
    summary_id = compaction.summary_message_id
    summary = next(e for e in events if isinstance(e, MessageEvent) and e.message_id == summary_id)
    assert CANARIES[0][3] in summary.content
    assert CANARIES[1][3] not in summary.content and "EU region" in summary.content
    assert CANARIES[2][3] not in summary.content


def test_compaction_precedes_its_summary_message() -> None:
    events = trace()
    compaction = next(e for e in events if isinstance(e, CompactionEvent))
    summary_seq = next(
        e.seq for e in events if isinstance(e, MessageEvent) and e.origin == "summary"
    )
    assert compaction.seq < summary_seq


def test_every_tool_call_has_a_result() -> None:
    events = trace()
    calls = {e.call_id for e in events if e.type == "tool_call"}
    results = {e.call_id for e in events if e.type == "tool_result"}
    assert calls and calls == results


def test_jsonl_round_trips_through_parse_event(tmp_path: Path) -> None:
    events = trace()
    path = tmp_path / "t.jsonl"
    write_jsonl(events, path)
    lines = path.read_text(encoding="utf-8").splitlines()
    assert [parse_event(line) for line in lines] == events
    assert all(json.loads(line)["run_id"] == "synthetic-001" for line in lines)
