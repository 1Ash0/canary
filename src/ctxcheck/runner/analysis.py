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


def label_of(row: dict[str, Any]) -> str:
    """`control`, or `treatment(llm_summary)`: policy rows are told apart by their policy."""
    policy = row.get("policy")
    return row["condition"] if policy is None else f"{row['condition']}({policy})"


def default_primary(labels: set[str]) -> list[tuple[str, str]]:
    """Each treatment against the full-context control and against its own length-matched twin."""
    pairs: list[tuple[str, str]] = []
    for label in sorted(labels):
        if label.startswith("treatment"):
            pairs.append((label, "control"))
            pairs.append((label, label.replace("treatment", "length_matched", 1)))
    return [(a, b) for a, b in pairs if a in labels and b in labels]


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
    invalid = sum(r.get("summary_valid") is False for r in rows)
    if invalid:
        out["n_summary_invalid"] = invalid  # summaries that echo the transcript (audit flag)
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
    a: dict[tuple, dict],
    b: dict[tuple, dict],
    na_violates: bool,
    valid_summaries_only: bool = False,
) -> list[tuple[bool, bool]]:
    def failed(row: dict[str, Any]) -> bool | None:
        if row["grade"] == "not_applicable":
            return True if na_violates else None
        return row["grade"] == "violated"

    out = []
    for key in sorted(a.keys() & b.keys()):
        if valid_summaries_only and (a[key].get("summary_valid") is False
                                     or b[key].get("summary_valid") is False):
            continue
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
    primary: Sequence[tuple[str, str]] | None = None,
    bootstrap_seed: int = 0,
) -> dict[str, Any]:
    """Cells per (model, window limit, condition/policy) and paired comparisons within each group.

    `primary` names the comparisons to run as pairs of labels (see `label_of`); by default every
    treatment is compared with `control` and with its length-matched twin.
    """
    if not rows:
        raise ValueError("no episodes to analyse")
    sources = {r["source"] for r in rows}
    if len(sources) != 1:
        raise ValueError(f"refusing to mix sources {sorted(sources)}: simulated is never measured")

    groups: dict[tuple, list[dict]] = defaultdict(list)
    for r in rows:
        groups[(r["model_requested"], r.get("limit_tokens"))].append(r)

    cells: list[dict[str, Any]] = []
    comparisons: list[dict[str, Any]] = []
    for (model, limit), group in sorted(groups.items(), key=lambda kv: (kv[0][0], kv[0][1] or 0)):
        by_label: dict[str, list[dict]] = defaultdict(list)
        for r in group:
            by_label[label_of(r)].append(r)
        for label, rs in sorted(by_label.items()):
            cells.append({"model": model, "limit_tokens": limit, "label": label,
                          "condition": rs[0]["condition"], "policy": rs[0]["policy"],
                          "prompt_version": rs[0]["prompt_version"], **_cell(rs)})
        keyed = {label: {(r["seed"], r["trial"]): r for r in rs} for label, rs in by_label.items()}
        for first, second in primary if primary is not None else default_primary(set(keyed)):
            if first not in keyed or second not in keyed:
                continue
            main = _compare(_pairs(keyed[first], keyed[second], False), bootstrap_seed)
            sens = _compare(_pairs(keyed[first], keyed[second], True), bootstrap_seed)
            valid = _compare(_pairs(keyed[first], keyed[second], False, True), bootstrap_seed)
            comparisons.append({"model": model, "limit_tokens": limit, "first": first,
                                "second": second, **main, "sensitivity_na_as_violated": sens,
                                "sensitivity_valid_summaries_only": valid})
    qs = benjamini_hochberg([c["p_mcnemar"] for c in comparisons])
    for c, q in zip(comparisons, qs, strict=True):
        c["q_bh"] = q

    first_row = rows[0]
    return {
        "exp_id": first_row["exp_id"], "pack": first_row["pack"], "source": next(iter(sources)),
        "models_reported": sorted({r["model_id_reported"] for r in rows}),
        "dates": sorted({r["date"] for r in rows}),
        "n_episodes": len(rows), "cells": cells, "comparisons": comparisons,
        "notes": ["rate = violated / graded episodes; not_applicable excluded and counted",
                  "q_bh adjusts all listed comparisons together (Benjamini-Hochberg)"],
    }
