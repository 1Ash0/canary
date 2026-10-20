"""Canary fate: a view derived by replaying the trace, never stored.

Rule (v0, deterministic): a planted fact is `kept` if its text appears verbatim in a message still
in the window at the end of the replay, otherwise `gone`. Case and punctuation matter: a paraphrase
counts as gone. `changed` is reserved for a labelled judge model (ADR-002) and is not produced here.
"""

from __future__ import annotations

import unicodedata
from collections.abc import Collection, Iterable
from typing import Literal

from ctxcheck.grading import fold_dashes
from ctxcheck.schema import (
    CanaryPlantedEvent,
    CompactionEvent,
    MessageEvent,
    RunStartEvent,
    TraceEvent,
)

Fate = Literal["kept", "gone"]


def _fold(text: str) -> str:
    """Compare modulo compatibility forms and dash variants only. Case still matters. A model's
    non-breaking hyphen in a channel name must not make a kept fact look gone (owner's audit)."""
    return fold_dashes(unicodedata.normalize("NFKC", text))


def derive_fates(
    events: Iterable[TraceEvent], exclude: Collection[str] = ()
) -> dict[str, Fate]:
    """`exclude` names messages that must not count as survival, such as the probe turn: a probe
    may legitimately mention the planted value (a list of channels), which is not the fact itself.
    """
    ordered = sorted(events, key=lambda e: e.seq)
    if not ordered or not isinstance(ordered[0], RunStartEvent):
        raise ValueError("trace must begin with run_start")

    live: dict[str, str] = {}  # message_id -> content currently in the window
    planted: dict[str, str] = {}  # canary_id -> the planted text
    for event in ordered[1:]:
        if isinstance(event, MessageEvent):
            live[event.message_id] = event.content
        elif isinstance(event, CanaryPlantedEvent):
            planted[event.canary_id] = event.value
        elif isinstance(event, CompactionEvent):
            for message_id in event.dropped_ids:
                if message_id not in live:
                    raise ValueError(f"compaction drops unknown message {message_id!r}")
                del live[message_id]

    window = [_fold(text) for message_id, text in live.items() if message_id not in exclude]
    return {
        cid: "kept" if any(_fold(value) in text for text in window) else "gone"
        for cid, value in planted.items()
    }


def survival_at_probe(events: list[TraceEvent], canary_id: str, probe_message_id: str) -> Fate:
    """Is the planted fact still verbatim in the window the probe call saw?

    Judged before the first model call after the compaction (or after the probe, if the window was
    never compacted): the agent's own reply may repeat the value, and so may the probe (a channel
    list), and neither is the fact surviving.
    """
    compaction = next((e for e in events if e.type == "compaction"), None)
    probe = next(e for e in events if isinstance(e, MessageEvent)
                 and e.message_id == probe_message_id)
    anchor = compaction.seq if compaction else probe.seq
    cut = next((e.seq for e in events if e.type == "model_call" and e.seq > anchor), None)
    window = [e for e in events if cut is None or e.seq < cut]
    return derive_fates(window, exclude={probe_message_id})[canary_id]
