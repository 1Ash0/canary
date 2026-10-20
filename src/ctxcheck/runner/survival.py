"""Mechanical survival grid: does the planted fact survive each deterministic policy?

No model is involved. The history is a seeded synthetic scenario and the policy is the real policy
code, so for a given (policy, canary position, budget, seed) the outcome is exact and reproducible.
The grid answers "what does this policy keep" and nothing about how an agent behaves afterwards;
that needs a model (the experiments). Its epistemic tag is `deterministic`: real policy code on a
synthetic history, not recorded model output, not simulated behaviour.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from ctxcheck.canaries import build_pack
from ctxcheck.harness.loop import run
from ctxcheck.harness.types import ModelResponse, ToolCall
from ctxcheck.policies import make_policy
from ctxcheck.providers.scripted import ScriptedProvider
from ctxcheck.runner.episode import survival_at_probe
from ctxcheck.schema import MessageEvent
from ctxcheck.stats import wilson_interval

DEFAULT_POLICIES = ("recency_truncate", "head_tail", "observation_mask")


def _stub_probe_reply(tool: str, args: dict[str, Any]) -> ModelResponse:
    return ModelResponse(tool_call=ToolCall("stub", tool, args))


def survival_grid(
    pack: str = "constraint",
    policies: Sequence[str] = DEFAULT_POLICIES,
    positions: Sequence[int] = (0, 3, 6, 9, 12, 15, 17),
    budgets: Sequence[int] = (1200, 1800, 2400, 3000, 3600),
    seeds: int = 20,
    n_filler: int = 18,
) -> dict[str, Any]:
    cells = []
    for policy in policies:
        for position in positions:
            for budget in budgets:
                kept = n = 0
                for seed in range(1, seeds + 1):
                    built = build_pack(pack, seed, n_filler=n_filler, canary_turn=position)
                    args = {p: "x" for p in built.tools[-1].spec.input_schema["properties"]}
                    events = run(built.scenario,
                                 ScriptedProvider([_stub_probe_reply(built.spec.tool_name, args)]),
                                 built.tools, limit_tokens=budget, policy=make_policy(policy),
                                 clock=lambda: "t", run_id="survival")
                    if not any(e.type == "compaction" for e in events):
                        continue  # the window fit: nothing was compacted, so nothing to report
                    probe = next(e for e in events if isinstance(e, MessageEvent)
                                 and e.step == built.probe_step and e.role == "user")
                    n += 1
                    kept += survival_at_probe(events, built.spec.canary_id,
                                              probe.message_id) == "kept"
                lo, hi = wilson_interval(kept, n) if n else (None, None)
                cells.append({"policy": policy, "position": position, "budget": budget,
                              "k_kept": kept, "n": n, "rate": kept / n if n else None,
                              "wilson_lo": lo, "wilson_hi": hi})
    return {
        "epistemic": "deterministic",
        "description": "Real policy code on seeded synthetic histories. No model was called.",
        "pack": pack, "n_filler_turns": n_filler, "seeds_per_cell": seeds,
        "positions": list(positions), "budgets": list(budgets), "policies": list(policies),
        "cells": cells,
    }
