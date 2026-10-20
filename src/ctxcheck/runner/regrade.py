"""Re-derive each episode's grade, survival and summary validity from its trace.

Traces are the source of truth; rows are a cache of what the checks said at the time. When a check
is corrected (ADR-020 amendments), regrading shows exactly which rows change and why, without
calling a model again.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ctxcheck.canaries import build_pack
from ctxcheck.grading import grade_trace
from ctxcheck.runner.episode import summary_truncation, summary_validity, survival_at_probe
from ctxcheck.runner.trace_io import read_trace
from ctxcheck.schema import MessageEvent

FIELDS = ("grade", "evidence", "canary_fate", "summary_valid", "summary_truncated")


@dataclass
class Regrade:
    rows: list[dict[str, Any]] = field(default_factory=list)
    changes: list[tuple[str, int, str, str, Any, Any]] = field(default_factory=list)


def regrade_rows(rows: list[dict[str, Any]], root: Path = Path(".")) -> Regrade:
    out = Regrade()
    for r in rows:
        events = read_trace(root / r["trace_path"])
        built = build_pack(r["pack"], r["seed"], plant=r["condition"] != "floor")
        probe_text = built.scenario.turns[-1].text
        probe = next(e for e in events if isinstance(e, MessageEvent) and e.role == "user"
                     and e.content == probe_text)
        graded = grade_trace(events, built.spec, after_seq=probe.seq)
        compacted = any(e.type == "compaction" for e in events)
        fate = (survival_at_probe(events, built.spec.canary_id, probe.message_id)
                if compacted and built.planted else None)
        new = {**r, "grade": graded.grade, "evidence": graded.evidence, "canary_fate": fate,
               "summary_valid": summary_validity(events),
               "summary_truncated": summary_truncation(events)}
        for key in FIELDS:
            if new[key] != r.get(key):
                out.changes.append((r["model_requested"], r["seed"], r["condition"], key,
                                    r.get(key), new[key]))
        out.rows.append(new)
    return out


def read_rows(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows),
                    encoding="utf-8", newline="\n")
