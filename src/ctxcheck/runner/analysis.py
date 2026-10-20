"""From episode rows to the numbers a report may state: rates with intervals and paired tests.

Violation is the outcome (`grade == "violated"`). Episodes with no accepted call to the watched
tool (`not_applicable`) are never silently dropped: they are counted in every cell, excluded from
the rate, and a sensitivity analysis recomputes each comparison counting them as violations.
Simulated and recorded rows are never mixed: that is an error, not a warning.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from typing import Any

from ctxcheck.stats import benjamini_hochberg, mcnemar_exact, paired_bootstrap_rd, wilson_interval

DEFAULT_PRIMARY = (("treatment", "control"), ("treatment", "length_matched"))


def _cell(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    graded = [r for r in rows if r["grade"] != "not_applicable"]
    k = sum(r["grade"] == "violated" for r in graded)
    out: dict[str, Any] = {
        "n_episodes": len(rows), "n_graded": len(graded), "k_violated": k,
        "n_not_applicable": len(rows) - len(graded),
    }
    if graded:
        lo, hi = wilson_interval(k, len(graded))
        out.update(rate=k / len(graded), wilson_lo=lo, wilson_hi=hi)
    compacted = [r for r in rows if r.get("canary_fate") is not None]
    if compacted:
        kept = sum(r["canary_fate"] == "kept" for r in compacted)
        lo, hi = wilson_interval(kept, len(compacted))
        out["verbatim_survival"] = {
            "k_kept": kept, "n": len(compacted), "rate": kept / len(compacted),
            "wilson_lo": lo, "wilson_hi": hi,
        }
    return out


def _pairs(
    a: dict[tuple, dict], b: dict[tuple, dict], na_violates: bool
) -> list[tuple[bool, bool]]:
    def failed(row: dict[str, Any]) -> bool | None:
        if row["grade"] == "not_applicable":
            return True if na_violates else None
        return row["grade"] == "violated"

    out = []
    for key in sorted(a.keys() & b.keys()):
        x, y = failed(a[key]), failed(b[key])
        if x is not None and y is not None:
            out.append((x, y))
    return out


def _compare(pairs: list[tuple[bool, bool]], seed: int) -> dict[str, Any]:
    only_a = sum(x and not y for x, y in pairs)
    only_b = sum(y and not x for x, y in pairs)
    out: dict[str, Any] = {"n_pairs": len(pairs), "only_first_failed": only_a,
                           "only_second_failed": only_b, "p_mcnemar": mcnemar_exact(only_a, only_b)}
    if len(pairs) >= 2:
        rd, lo, hi = paired_bootstrap_rd(pairs, seed=seed)
        out.update(risk_difference=rd, rd_lo=lo, rd_hi=hi)
    return out


def analyse(
    rows: Sequence[dict[str, Any]],
    primary: Sequence[tuple[str, str]] = DEFAULT_PRIMARY,
    bootstrap_seed: int = 0,
) -> dict[str, Any]:
    if not rows:
        raise ValueError("no episodes to analyse")
    sources = {r["source"] for r in rows}
    if len(sources) != 1:
        raise ValueError(f"refusing to mix sources {sorted(sources)}: simulated is never measured")

    by_cell: dict[tuple, list[dict]] = defaultdict(list)
    for r in rows:
        by_cell[(r["model_requested"], r["condition"])].append(r)
    cells = [{"model": m, "condition": c, "policy": rs[0]["policy"],
              "prompt_version": rs[0]["prompt_version"], **_cell(rs)}
             for (m, c), rs in sorted(by_cell.items())]

    comparisons: list[dict[str, Any]] = []
    for model in sorted({r["model_requested"] for r in rows}):
        keyed = {c: {(r["seed"], r["trial"]): r for r in rows
                     if r["model_requested"] == model and r["condition"] == c}
                 for c in ("floor", "control", "length_matched", "treatment")}
        for first, second in primary:
            main = _compare(_pairs(keyed[first], keyed[second], False), bootstrap_seed)
            sens = _compare(_pairs(keyed[first], keyed[second], True), bootstrap_seed)
            comparisons.append({"model": model, "first": first, "second": second, **main,
                                "sensitivity_na_as_violated": sens})
    qs = benjamini_hochberg([c["p_mcnemar"] for c in comparisons])
    for c, q in zip(comparisons, qs, strict=True):
        c["q_bh"] = q

    first = rows[0]
    return {
        "exp_id": first["exp_id"], "pack": first["pack"], "source": next(iter(sources)),
        "models_reported": sorted({r["model_id_reported"] for r in rows}),
        "dates": sorted({r["date"] for r in rows}),
        "n_episodes": len(rows), "cells": cells, "comparisons": comparisons,
        "notes": ["rate = violated / graded episodes; not_applicable excluded and counted",
                  "q_bh adjusts the primary comparisons together (Benjamini-Hochberg)"],
    }
