"""Mock experiment for the M1 playground: control vs recency_truncate, n seeded trials each.

NOTHING HERE IS MEASURED. Each trial's outcome is a seeded random draw using the *assumed* violation
rates below; no model was called. The output says so on its face (`epistemic: "simulated"`) and a
consumer must label it `mock data`. It exists so the site can show intervals and a paired table
before a real run exists (M4).
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path
from typing import Any

from ctxcheck.stats import wilson_interval

ASSUMED_RATES = {"control": 0.05, "recency_truncate": 0.40}  # assumptions, not findings


def run_mock(seed: int = 1, n: int = 10) -> dict[str, Any]:
    rnd = random.Random(seed)
    trials = []
    for trial_seed in range(1, n + 1):
        outcome = {
            condition: "violated" if rnd.random() < rate else "respected"
            for condition, rate in ASSUMED_RATES.items()
        }
        trials.append({"seed": trial_seed, **outcome})

    cells = {}
    for condition in ASSUMED_RATES:
        k = sum(t[condition] == "violated" for t in trials)
        lo, hi = wilson_interval(k, n)
        cells[condition] = {"k": k, "n": n, "rate": k / n, "wilson_lo": lo, "wilson_hi": hi}

    both = sum(t["control"] == "violated" and t["recency_truncate"] == "violated" for t in trials)
    only_treatment = sum(
        t["control"] == "respected" and t["recency_truncate"] == "violated" for t in trials
    )
    only_control = sum(
        t["control"] == "violated" and t["recency_truncate"] == "respected" for t in trials
    )
    return {
        "epistemic": "simulated",
        "label": "mock data",
        "note": "Outcomes are seeded random draws at the assumed rates. No model was called.",
        "seed": seed,
        "assumed_rates": ASSUMED_RATES,
        "cells": cells,
        "paired": {  # concordant pairs carry no information about the difference
            "both_violated": both,
            "both_respected": n - both - only_treatment - only_control,
            "only_treatment_violated": only_treatment,
            "only_control_violated": only_control,
        },
        "trials": trials,
    }


if __name__ == "__main__":  # python -m ctxcheck.mock_experiment results/samples/mock_exp_001.json
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "results/samples/mock_exp_001.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(run_mock(), indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out}")
