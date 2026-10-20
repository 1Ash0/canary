"""Tally an owner's hand audit against the machine's verdicts, the agent's behaviour and truncation.

Input: JSON list of {"model", "seed", "call", "note"}; call is verbatim, reworded, dropped or echo.
`present` = the owner judged the rule still usable (verbatim or reworded). `machine_kept` = the
planted channel name appears in the summary (modulo dash variants, ADR-021). `truncated` = the
summary call stopped at the token cap (`finish_reason: length`), read from the cassettes.

    python scripts/audit_tally.py                      # the 10-seed pilot audit
    python scripts/audit_tally.py --audit nvidia       # the 27-seed NVIDIA audit
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AUDITS = {
    "pilot": ("docs/audit/EXP-001-audit-calls.json",
              "results/EXP-001-pilot10-reanalysed/episodes.jsonl",
              "results/EXP-001-pilot10-reanalysed/audit_tally.json",
              ["cassettes/EXP-001", "cassettes/EXP-001-pilot10"]),
    "nvidia": ("docs/audit/EXP-001-audit-calls-nvidia.json",
               "results/EXP-001/episodes.jsonl",
               "results/EXP-001/audit_tally_nvidia.json",
               ["cassettes/EXP-001"]),
}
PRESENT = {"verbatim", "reworded"}


def finish_reasons(dirs: list[str]) -> dict[str, str]:
    """Summary text -> finish reason, for every recorded summary call (no tools offered)."""
    out: dict[str, str] = {}
    for d in dirs:
        for f in (ROOT / d).rglob("*.json"):
            entry = json.loads(f.read_text(encoding="utf-8"))
            if entry["request"]["tools"] == []:
                out[entry["response"]["text"].strip()] = entry["response"]["extra"].get(
                    "finish_reason", "unknown")
    return out


def summary_text(trace_path: str) -> str | None:
    for line in (ROOT / trace_path).read_text(encoding="utf-8").splitlines():
        e = json.loads(line)
        if e.get("type") == "message" and e.get("origin") == "summary":
            return e["content"].split("\n", 1)[1].strip()
    return None


def tally(audit: str) -> dict:
    calls_path, rows_path, out_path, cassette_dirs = AUDITS[audit]
    calls = json.loads((ROOT / calls_path).read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in (ROOT / rows_path).read_text(encoding="utf-8").splitlines()
            if line]
    treatment = {(r["model_requested"], r["seed"]): r
                 for r in rows if r["condition"] == "treatment"}
    reasons = finish_reasons(cassette_dirs)

    per_model: dict[str, dict] = {}
    for c in calls:
        row = treatment[(c["model"], c["seed"])]
        m = per_model.setdefault(c["model"], {
            "calls": Counter(), "summaries_judged": 0, "machine_agrees_rule_present": 0,
            "machine_disagrees_rule_present": 0, "echo_called_by_owner": 0,
            "echo_flagged_by_machine": 0, "behaviour_follows_owner_call": 0,
            "behaviour_judged": 0, "failed_summaries": 0, "truncated": 0,
            "truncated_rule_present": 0, "complete": 0, "complete_rule_present": 0})
        m["calls"][c["call"]] += 1
        if row["summary_valid"] is None:  # the summarizer call failed: no summary to judge
            m["failed_summaries"] += 1
            continue
        if c["call"] == "echo":
            m["echo_called_by_owner"] += 1
            m["echo_flagged_by_machine"] += row["summary_valid"] is False
            continue
        owner_present = c["call"] in PRESENT
        m["summaries_judged"] += 1
        if owner_present == (row["canary_fate"] == "kept"):
            m["machine_agrees_rule_present"] += 1
        else:
            m["machine_disagrees_rule_present"] += 1
        m["behaviour_judged"] += 1
        m["behaviour_follows_owner_call"] += owner_present == (row["grade"] == "respected")
        text = summary_text(row["trace_path"])
        cut = reasons.get(text or "") == "length"
        m["truncated" if cut else "complete"] += 1
        m["truncated_rule_present" if cut else "complete_rule_present"] += owner_present
    for m in per_model.values():
        m["calls"] = dict(m["calls"])
    total: Counter = Counter()
    for m in per_model.values():
        for key, value in m.items():
            if isinstance(value, int):
                total[key] += value
    result = {"per_model": per_model, "total": dict(total), "n_calls": len(calls)}
    (ROOT / out_path).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8",
                                 newline="\n")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit", choices=sorted(AUDITS), default="pilot")
    print(json.dumps(tally(parser.parse_args().audit)["total"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
