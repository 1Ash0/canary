"""Token ledger: a view derived by replaying trace events (never stored).
The question it answers: what was in the context window at the end of each step, split by layer?
One row per step. A compaction event is applied when it is replayed, so it changes the *next*
step's row.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Literal

from ctxcheck.schema import (
    CompactionEvent,
    MessageEvent,
    RunStartEvent,
    TraceEvent,
)

Layer = Literal["system", "tools", "history", "toolOutput", "summary"]
LAYERS: tuple[Layer, ...] = ("system", "tools", "history", "toolOutput", "summary")


def layer_of(message: MessageEvent) -> Layer:
    if message.origin == "summary":
        return "summary"
    if message.role == "system":
        return "system"
    if message.role == "tool" or message.origin == "tool":
        return "toolOutput"
    return "history"


@dataclass(frozen=True)
class LedgerRow:
    step: int
    layers: dict[Layer, int]

    @property
    def total(self) -> int:
        return sum(self.layers.values())


@dataclass(frozen=True)
class CompactionRecord:
    after_step: int  # last step before the compaction
    tokens_before: int
    tokens_after: int


@dataclass
class Ledger:
    run_id: str
    limit_tokens: int
    rows: list[LedgerRow] = field(default_factory=list)
    compactions: list[CompactionRecord] = field(default_factory=list)


def replay(events: Iterable[TraceEvent]) -> Ledger:
    """Replay events in `seq` order into a ledger. Raises ValueError on a malformed trace."""
    ordered = sorted(events, key=lambda e: e.seq)
    if not ordered or not isinstance(ordered[0], RunStartEvent):
        raise ValueError("trace must begin with run_start")
    start = ordered[0]
    ledger = Ledger(run_id=start.run_id, limit_tokens=start.limit_tokens)

    live: dict[str, MessageEvent] = {}  # messages currently in the window, by id
    current_step = 0
    last_row_step = 0

    def snapshot(step: int) -> LedgerRow:
        layers: dict[Layer, int] = dict.fromkeys(LAYERS, 0)
        layers["tools"] = start.tools_tokens_est
        for m in live.values():
            layers[layer_of(m)] += m.tokens_est
        return LedgerRow(step, layers)

    def close_step() -> None:
        nonlocal last_row_step
        if current_step > last_row_step:
            ledger.rows.append(snapshot(current_step))
            last_row_step = current_step

    for event in ordered[1:]:
        if isinstance(event, MessageEvent):
            if event.step < current_step:
                raise ValueError(f"message step went backwards at seq {event.seq}")
            if event.step > current_step:
                close_step()
                current_step = event.step
            live[event.message_id] = event
        elif isinstance(event, CompactionEvent):
            close_step()
            for message_id in event.dropped_ids:
                if message_id not in live:
                    raise ValueError(f"compaction drops unknown message {message_id!r}")
                del live[message_id]
            ledger.compactions.append(
                CompactionRecord(current_step, event.tokens_before, event.tokens_after)
            )
    close_step()
    return ledger
