"""Reading and writing JSONL traces. One event per line, validated on the way in and out."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from ctxcheck.schema import TraceEvent, parse_event


def write_trace(path: Path, events: Iterable[TraceEvent]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # newline="\n" and utf-8: the same bytes on Windows and Linux, so replays can be diffed
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for e in events:
            f.write(e.model_dump_json() + "\n")


def read_trace(path: Path) -> list[TraceEvent]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return [parse_event(line) for line in lines if line.strip()]
