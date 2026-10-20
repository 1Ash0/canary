"""The experiment matrix: (seed x trial x condition), resumable, one result row per episode.

Rows are appended to `episodes.jsonl` the moment an episode finishes, so a crash or a budget stop
loses nothing and a rerun skips every cell already present (the cell key is stable). A budget stop
or a provider failure ends the run cleanly with partial results; nothing is retried at this layer.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterator
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Any

from ctxcheck.canaries import build_pack, window_tokens_before_probe
from ctxcheck.harness.budget import BudgetError
from ctxcheck.providers.base import Provider
from ctxcheck.providers.cassette import CassetteMiss
from ctxcheck.runner.episode import CONDITIONS, EpisodeRow, EpisodeSpec, run_episode


@dataclass(frozen=True)
class ExperimentPlan:
    exp_id: str
    pack: str
    policy: str
    seeds: tuple[int, ...]
    trials: int = 1
    conditions: tuple[str, ...] = CONDITIONS
    policy_options: tuple[tuple[str, Any], ...] = ()
    limit_tokens: int = 2400
    n_filler: int = 18
    lines: int = 10
    canary_turn: int = 1
    params: tuple[tuple[str, Any], ...] = ()

    def cells(self) -> Iterator[EpisodeSpec]:
        # treatment before length_matched: the latter is sized from the former's result
        order = [c for c in ("floor", "control", "treatment", "length_matched")
                 if c in self.conditions]
        for seed in self.seeds:
            for trial in range(self.trials):
                for condition in order:
                    has_policy = condition in ("treatment", "length_matched")
                    yield EpisodeSpec(
                        self.exp_id, self.pack, condition, seed, trial,
                        policy=self.policy if has_policy else None,
                        policy_options=self.policy_options if has_policy else (),
                        limit_tokens=self.limit_tokens, n_filler=self.n_filler, lines=self.lines,
                        canary_turn=self.canary_turn, params=self.params)

    def calls_upper_bound(self) -> int:
        """Most model calls the plan can make: one probe each, plus one summary for llm_summary."""
        extra = 1 if self.policy == "llm_summary" and "treatment" in self.conditions else 0
        per_pair = len(self.conditions) + extra
        return len(self.seeds) * self.trials * per_pair


def estimate_tokens(plan: ExperimentPlan) -> tuple[int, int]:
    """Rough (input, output) tokens for the whole plan, from a sample episode. Upper-bound style."""
    sample = build_pack(plan.pack, plan.seeds[0], n_filler=plan.n_filler, lines=plan.lines,
                        canary_turn=plan.canary_turn)
    full = window_tokens_before_probe(sample)
    per_seed = 0
    for c in plan.conditions:
        per_seed += full if c in ("floor", "control") else plan.limit_tokens
    if plan.policy == "llm_summary" and "treatment" in plan.conditions:
        per_seed += full  # the summary call reads the whole history
    n = len(plan.seeds) * plan.trials
    out_tokens = n * (len(plan.conditions) * 80 + (400 if plan.policy == "llm_summary" else 0))
    return n * per_seed, out_tokens


@dataclass
class RunReport:
    ran: int = 0
    skipped: int = 0
    missing_cassettes: list[str] = field(default_factory=list)
    stopped: str | None = None  # why the run ended early, if it did
    rows: list[EpisodeRow] = field(default_factory=list)


def read_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def run_experiment(
    plan: ExperimentPlan,
    provider: Provider,
    *,
    provider_name: str,
    model: str,
    out_dir: Path,
    runs_dir: Path,
    source: str = "recorded",
    log: Callable[[str], None] = lambda _: None,
) -> RunReport:
    out_dir.mkdir(parents=True, exist_ok=True)
    episodes = out_dir / "episodes.jsonl"
    done = {r["key"]: r for r in read_rows(episodes)}
    report = RunReport()
    for spec in plan.cells():
        if spec.key in done:
            report.skipped += 1
            continue
        matched = None
        if spec.condition == "length_matched":
            twin = replace(spec, condition="treatment")
            if twin.key not in done:
                log(f"skip {spec.key}: its treatment episode has no result yet")
                continue
            matched = int(done[twin.key]["window_at_probe"])
        try:
            row = run_episode(spec, provider, provider_name=provider_name, model=model,
                              runs_dir=runs_dir, matched_tokens=matched, source=source)
        except CassetteMiss:
            report.missing_cassettes.append(spec.key)
            continue
        except BudgetError as e:
            report.stopped = f"budget: {e}"
            break
        except Exception as e:  # a provider failure after retries: stop, keep what we have
            report.stopped = f"{type(e).__name__}: {e}"
            break
        with episodes.open("a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(asdict(row), sort_keys=True) + "\n")
        done[row.key] = asdict(row)
        report.ran += 1
        report.rows.append(row)
        log(f"{spec.condition:<14} seed={spec.seed} trial={spec.trial} -> {row.grade}")
    return report
