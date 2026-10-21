"""Tally a per-fact audit of multi-pack summaries (EXP-004): one call per fact per seed.

Input: docs/audit/<exp>-audit-calls-multi.json, a list of {"seed", "auditor", "blind", "calls":
{"C1": ..., "I1": ..., "D1": ...}, "note"}; calls are verbatim, reworded, dropped or echo. For each
fact: how often the call agrees with the machine's survival check (the fact's fate in the trace),
and how often the agent's grade on that fact's request matches the call (present and right, or
absent and wrong). The auditor and whether the audit was blind are carried into the output.

    python scripts/audit_tally_multi.py EXP-004
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACK = {"C1": "multi_channel", "I1": "multi_code", "D1": "multi_deploy"}
PRESENT = {"verbatim", "reworded"}


def main() -> int:
    exp = sys.argv[1]
    calls_path = ROOT / f"docs/audit/{exp}-audit-calls-multi.json"
    calls = json.loads(calls_path.read_text(encoding="utf-8"))
    lines = (ROOT / f"results/{exp}/episodes.jsonl").read_text(encoding="utf-8").splitlines()
    rows = [json.loads(line) for line in lines if line]
    summ = {(r["pack"], r["seed"]): r for r in rows
            if r["condition"] == "treatment" and r["policy"] == "llm_summary"}
    out: dict = {"exp_id": exp, "auditor": calls[0]["auditor"], "blind": calls[0]["blind"],
                 "facts": {}, "disagreements": []}
    for fact, pack in PACK.items():
        t = {"judged": 0, "machine_agrees": 0, "behaviour_judged": 0, "behaviour_follows": 0,
             "calls": {}}
        for c in calls:
            call = c["calls"][fact]
            t["calls"][call] = t["calls"].get(call, 0) + 1
            row = summ[(pack, c["seed"])]
            present = call in PRESENT
            t["judged"] += 1
            machine = (row.get("fates") or {}).get(fact) == "kept"
            t["machine_agrees"] += present == machine
            if present != machine:
                out["disagreements"].append({"fact": fact, "seed": c["seed"], "call": call,
                                             "machine": "kept" if machine else "gone"})
            if row["grade"] != "not_applicable":
                t["behaviour_judged"] += 1
                t["behaviour_follows"] += present == (row["grade"] == "respected")
        out["facts"][fact] = t
    path = ROOT / f"results/{exp}/audit_tally.json"
    path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
