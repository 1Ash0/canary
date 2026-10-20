"""One episode: build the scenario for a condition, run it, grade it, write the trace.

An episode is one (seed, trial, condition) cell. The four conditions (EVAL_DESIGN §3):
  floor           no canary planted, no compaction: what the model does without the fact
  control         canary planted, full context, no compaction: should respect it
  length_matched  canary planted, no compaction, filler trimmed to the treatment's post-compaction
                  size: separates "a shorter window" from "a damaged canary"
  treatment       canary planted, the policy compacts the window, then the probe
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ctxcheck.canaries import build_pack, trim_to_length, window_tokens_before_probe
from ctxcheck.fates import derive_fates
from ctxcheck.grading import grade_trace
from ctxcheck.harness.loop import run
from ctxcheck.policies import make_policy
from ctxcheck.providers.base import Provider
from ctxcheck.runner.trace_io import write_trace
from ctxcheck.schema import CanaryProbeEvent, MessageEvent, TraceEvent

CONDITIONS = ("floor", "control", "length_matched", "treatment")


@dataclass(frozen=True)
class EpisodeSpec:
    exp_id: str
    pack: str
    condition: str
    seed: int
    trial: int
    policy: str | None = None  # treatment only
    policy_options: tuple[tuple[str, Any], ...] = ()
    limit_tokens: int = 2400
    n_filler: int = 18
    lines: int = 10
    canary_turn: int = 1
    params: tuple[tuple[str, Any], ...] = ()

    def __post_init__(self) -> None:
        if self.condition not in CONDITIONS:
            raise ValueError(f"unknown condition {self.condition!r}")
        if (self.condition == "treatment") != (self.policy is not None):
            raise ValueError("a policy is required for the treatment condition and only then")

    @property
    def key(self) -> str:
        """Stable id of the cell: the same spec always has the same key (resume relies on it)."""
        blob = json.dumps(asdict(self), sort_keys=True, default=str)
        return hashlib.sha256(blob.encode()).hexdigest()[:16]


@dataclass
class EpisodeRow:
    """One line of results/<exp>/episodes.jsonl."""

    exp_id: str
    key: str
    pack: str
    condition: str
    policy: str | None
    prompt_version: str | None
    seed: int
    trial: int
    provider: str
    model_requested: str
    model_id_reported: str
    grade: str
    evidence: str
    canary_fate: str | None  # verbatim survival in the window at the probe; None if not compacted
    compacted: bool
    window_at_probe: int  # tokens in the window when the probe call was made
    tokens_before: int | None
    tokens_after: int | None
    model_calls: int
    summary_calls: int
    run_reason: str
    source: str  # "recorded" or "simulated"; never blank
    date: str
    run_id: str
    trace_path: str
    params: dict[str, Any] = field(default_factory=dict)


def _probe_event(events: list[TraceEvent], spec_grade: Any, canary_id: str,
                 probe_step: int) -> CanaryProbeEvent:
    probe_msg = next(e for e in events if isinstance(e, MessageEvent)
                     and e.step == probe_step and e.role == "user")
    end = events[-1]
    return CanaryProbeEvent(
        run_id=end.run_id, seq=end.seq, ts=end.ts, type="canary_probe", canary_id=canary_id,
        probe_message_id=probe_msg.message_id, grade=spec_grade.grade, evidence=spec_grade.evidence,
    )


def run_episode(
    spec: EpisodeSpec,
    provider: Provider,
    *,
    provider_name: str,
    model: str,
    runs_dir: Path,
    matched_tokens: int | None = None,
    source: str = "recorded",
    clock: Callable[[], str] | None = None,
) -> EpisodeRow:
    built = build_pack(spec.pack, spec.seed, plant=spec.condition != "floor",
                       n_filler=spec.n_filler, lines=spec.lines, canary_turn=spec.canary_turn)
    if spec.condition == "length_matched":
        if matched_tokens is None:
            raise ValueError("length_matched needs the treatment's post-compaction size")
        built, _ = trim_to_length(built, matched_tokens)

    pre_probe = window_tokens_before_probe(built)
    policy = None
    if spec.condition == "treatment":
        assert spec.policy is not None
        policy = make_policy(spec.policy, **dict(spec.policy_options))
        limit = spec.limit_tokens
    else:  # never compacts: a limit comfortably above the window
        limit = max(spec.limit_tokens * 4, pre_probe + 512)

    kwargs: dict[str, Any] = {} if clock is None else {"clock": clock}
    events = run(built.scenario, provider, built.tools, limit_tokens=limit, policy=policy,
                 run_id=f"{spec.exp_id}-{spec.key}", seed=spec.seed, params=dict(spec.params),
                 trial_index=spec.trial, provider_name=provider_name, model=model, **kwargs)

    probe_msg = next(e for e in events if isinstance(e, MessageEvent)
                     and e.step == built.probe_step and e.role == "user")
    graded = grade_trace(events, built.spec, after_seq=probe_msg.seq)
    end = events[-1]
    assert end.type == "run_end"
    events = [*events[:-1], _probe_event(events, graded, built.spec.canary_id, built.probe_step),
              end.model_copy(update={"seq": end.seq + 1})]
    write_trace(runs_dir / f"{spec.exp_id}-{spec.key}.jsonl", events)

    compaction = next((e for e in events if e.type == "compaction"), None)
    calls = [e for e in events if e.type == "model_call"]
    # Survival is judged on the window the probe call saw: the agent's own reply may repeat the
    # value, and so may the probe (a channel list), and neither is the fact surviving.
    anchor = compaction.seq if compaction else probe_msg.seq
    cut = next((e.seq for e in events if e.type == "model_call" and e.seq > anchor), end.seq)
    fates = derive_fates([e for e in events if e.seq < cut], exclude={probe_msg.message_id})
    fate = fates.get(built.spec.canary_id) if compaction and built.planted else None
    return EpisodeRow(
        exp_id=spec.exp_id, key=spec.key, pack=spec.pack, condition=spec.condition,
        policy=spec.policy, prompt_version=getattr(policy, "prompt_version", None),
        seed=spec.seed, trial=spec.trial, provider=provider_name, model_requested=model,
        model_id_reported=calls[-1].model_id_reported if calls else "none",
        grade=graded.grade, evidence=graded.evidence, canary_fate=fate,
        compacted=compaction is not None,
        window_at_probe=compaction.tokens_after if compaction else pre_probe,
        tokens_before=compaction.tokens_before if compaction else None,
        tokens_after=compaction.tokens_after if compaction else None,
        model_calls=int(end.totals.get("model_calls", 0)),
        summary_calls=int(end.totals.get("summary_calls", 0)),
        run_reason=end.reason or "", source=source, date=datetime.now(UTC).date().isoformat(),
        run_id=end.run_id,
        trace_path=str((runs_dir / f"{spec.exp_id}-{spec.key}.jsonl").as_posix()),
        params=dict(spec.params),
    )
