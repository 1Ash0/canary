"""Adapter: trace events -> the JSON the scene reads (design/scene, site, video).

Pure functions. The scene never reads a raw trace; this is the one place that changes when the
trace schema does. Fate comes from `derive_fates` and the numbers from `replay`, so nothing is
computed twice.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from ctxcheck.fates import derive_fates, survival_at_probe
from ctxcheck.ledger import replay
from ctxcheck.schema import (
    CanaryPlantedEvent,
    CanaryProbeEvent,
    MessageEvent,
    RunStartEvent,
    TraceEvent,
)


def label_of(provider: str) -> str:
    """Epistemic label shown wherever the data is: synthetic data must never look recorded."""
    return "synthetic fixture" if provider == "synthetic" else "recorded"


def to_scene_input(events: Iterable[TraceEvent], source: str) -> dict[str, Any]:
    ordered = sorted(events, key=lambda e: e.seq)
    ledger = replay(ordered)
    probe = next((x for x in ordered if isinstance(x, CanaryProbeEvent)), None)
    if probe is None:
        fates = derive_fates(ordered)
    else:  # a run with a probe: judge survival at the probe, not at the end (the reply repeats it)
        fates = {e.canary_id: survival_at_probe(ordered, e.canary_id, probe.probe_message_id)
                 for e in ordered if isinstance(e, CanaryPlantedEvent)}
    start = ordered[0]
    assert isinstance(start, RunStartEvent)  # replay() already rejected anything else

    messages = {e.message_id: e for e in ordered if isinstance(e, MessageEvent)}
    canaries = []
    for e in ordered:
        if isinstance(e, CanaryPlantedEvent):
            canaries.append(
                {
                    "id": e.canary_id,
                    "type": e.canary_type,
                    "planted_step": messages[e.message_id].step,
                    "text": e.value,
                    "fate": fates[e.canary_id],
                    "after_text": None,  # reserved for a labelled judge ("changed")
                }
            )

    rows = [{"i": r.step, "layers": dict(r.layers)} for r in ledger.rows]
    compaction = None
    if ledger.compactions:
        at = ledger.compactions[0].after_step
        compaction = {"at_step": at, "after": dict(ledger.rows[at].layers)}

    return {
        "meta": {
            "label": label_of(start.provider),
            "run_id": start.run_id,
            "seed": start.seed,
            "model": None if start.provider == "synthetic" else start.model,
            "policy": start.policy,
            "limit_tokens": ledger.limit_tokens,
            "token_counts": "tokens_est: local tokenizer estimate, not provider-reported",
            "source": source,
            # a recorded episode's outcome: what the agent did when the probe arrived
            "probe": {"grade": probe.grade, "evidence": probe.evidence} if probe else None,
        },
        "steps": rows,
        "compaction": compaction,
        "canaries": canaries,
    }


def to_experiment(result: dict[str, Any], source: str) -> dict[str, Any]:
    """Experiment results pass through unchanged, plus provenance; the label is already in them."""
    return {**result, "source": source}
