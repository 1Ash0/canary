"""Tally the owner's hand audit against the machine's verdicts and the agent's behaviour.

Input: a JSON list of {"model", "seed", "call", "note"} where call is verbatim, reworded, dropped or
echo (docs/audit/EXP-001-audit-calls.json). The rows are the re-analysed 10-seed pilot.
Output: results/EXP-001-pilot10-reanalysed/audit_tally.json, which the docs quote through
docs/claims.json.

Reading the calls: `present` = the owner judged the rule still usable in the summary (verbatim or
reworded). `machine_kept` = the planted channel name appears in the summary (modulo dash variants).
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CALLS = ROOT / "docs/audit/EXP-001-audit-calls.json"
ROWS = ROOT / "results/EXP-001-pilot10-reanalysed/episodes.jsonl"
OUT = ROOT / "results/EXP-001-pilot10-reanalysed/audit_tally.json"
PRESENT = {"verbatim", "reworded"}


def main() -> int:
    calls = json.loads(CALLS.read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in ROWS.read_text(encoding="utf-8").splitlines() if line]
    treatment = {(r["model_requested"], r["seed"]): r
                 for r in rows if r["condition"] == "treatment"}

    per_model: dict[str, dict] = {}
    for c in calls:
        row = treatment[(c["model"], c["seed"])]
        m = per_model.setdefault(c["model"], {
            "calls": Counter(), "summaries_judged": 0, "machine_agrees_rule_present": 0,
            "machine_disagrees_rule_present": 0, "echo_called_by_owner": 0,
            "echo_flagged_by_machine": 0, "behaviour_follows_owner_call": 0,
            "behaviour_judged": 0, "failed_summaries": 0})
        m["calls"][c["call"]] += 1
        if row["summary_valid"] is None:  # the summarizer call failed: no summary to judge
            m["failed_summaries"] += 1
            continue
        if c["call"] == "echo":
            m["echo_called_by_owner"] += 1
            m["echo_flagged_by_machine"] += row["summary_valid"] is False
            continue
        m["summaries_judged"] += 1
        owner_present = c["call"] in PRESENT
        machine_present = row["canary_fate"] == "kept"
        if owner_present == machine_present:
            m["machine_agrees_rule_present"] += 1
        else:
            m["machine_disagrees_rule_present"] += 1
        m["behaviour_judged"] += 1
        m["behaviour_follows_owner_call"] += owner_present == (row["grade"] == "respected")
    for m in per_model.values():
        m["calls"] = dict(m["calls"])

    total = Counter()
    for m in per_model.values():
        for key, value in m.items():
            if isinstance(value, int):
                total[key] += value
    OUT.write_text(json.dumps({"per_model": per_model, "total": dict(total),
                               "n_calls": len(calls)}, indent=2) + "\n",
                   encoding="utf-8", newline="\n")
    print(json.dumps(dict(total)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
