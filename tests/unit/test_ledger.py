"""Ledger tests: replay must reproduce the window; malformed traces must be rejected."""

import pytest

from ctxcheck.ledger import LAYERS, layer_of, replay
from ctxcheck.schema import CompactionEvent, MessageEvent, RunEndEvent, RunStartEvent, TraceEvent

TS = "2026-10-20T00:00:00Z"


def start(seq: int = 0) -> RunStartEvent:
    return RunStartEvent(
        type="run_start", run_id="r", seq=seq, ts=TS, scenario_id="s", seed=1,
        policy="recency_truncate", provider="p", model="m", limit_tokens=1000, tools_tokens_est=50,
    )


def msg(seq: int, mid: str, step: int, tokens: int, role="user", origin="user") -> MessageEvent:
    return MessageEvent(
        type="message", run_id="r", seq=seq, ts=TS, message_id=mid, step=step, role=role,
        content="x", tokens_est=tokens, origin=origin,
    )


def compaction(seq: int, dropped: list[str], added: list[str] | None = None) -> CompactionEvent:
    return CompactionEvent(
        type="compaction", run_id="r", seq=seq, ts=TS, policy="recency_truncate", trigger="budget",
        tokens_before=0, tokens_after=0, kept_ids=[], dropped_ids=dropped, added_ids=added or [],
    )


def trace() -> list[TraceEvent]:
    return [
        start(),
        msg(1, "sys", 1, 100, role="system", origin="user"),
        msg(2, "u1", 1, 10),
        msg(3, "a1", 2, 20, role="assistant", origin="assistant"),
        msg(4, "t1", 3, 200, role="tool", origin="tool"),
        compaction(5, dropped=["u1", "a1", "t1"]),
        msg(6, "sum", 4, 30, role="user", origin="summary"),
        msg(7, "u2", 4, 5),
        RunEndEvent(type="run_end", run_id="r", seq=8, ts=TS, status="ok"),
    ]


def test_rows_grow_then_compaction_drops_the_next_row() -> None:
    ledger = replay(trace())
    assert [r.step for r in ledger.rows] == [1, 2, 3, 4]
    assert [r.total for r in ledger.rows] == [160, 180, 380, 185]  # 50 tools + live messages


def test_layers_split_by_role_and_origin() -> None:
    row3 = replay(trace()).rows[2].layers
    assert row3 == {"system": 100, "tools": 50, "history": 30, "toolOutput": 200, "summary": 0}
    row4 = replay(trace()).rows[3].layers
    assert row4["summary"] == 30 and row4["toolOutput"] == 0 and row4["history"] == 5


def test_every_row_has_every_layer() -> None:
    assert all(set(r.layers) == set(LAYERS) for r in replay(trace()).rows)


def test_compaction_is_recorded_between_steps() -> None:
    ledger = replay(trace())
    assert [c.after_step for c in ledger.compactions] == [3]


def test_replay_orders_by_seq_not_list_order() -> None:
    assert replay(list(reversed(trace()))).rows == replay(trace()).rows


def test_no_compaction_means_totals_only_grow() -> None:
    events = [e for e in trace() if not isinstance(e, CompactionEvent)][:5]
    totals = [r.total for r in replay(events).rows]
    assert totals == sorted(totals)


def test_trace_must_begin_with_run_start() -> None:
    with pytest.raises(ValueError, match="run_start"):
        replay([msg(0, "u1", 1, 5)])
    with pytest.raises(ValueError, match="run_start"):
        replay([])


def test_dropping_an_unknown_message_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown message"):
        replay([start(), msg(1, "u1", 1, 5), compaction(2, dropped=["ghost"])])


def test_step_going_backwards_is_rejected() -> None:
    with pytest.raises(ValueError, match="backwards"):
        replay([start(), msg(1, "a", 2, 5), msg(2, "b", 1, 5)])


@pytest.mark.parametrize(
    ("role", "origin", "layer"),
    [
        ("system", "user", "system"),
        ("user", "summary", "summary"),
        ("tool", "tool", "toolOutput"),
        ("user", "canary", "history"),
        ("assistant", "assistant", "history"),
    ],
)
def test_layer_of(role: str, origin: str, layer: str) -> None:
    assert layer_of(msg(1, "m", 1, 1, role=role, origin=origin)) == layer  # type: ignore[arg-type]
