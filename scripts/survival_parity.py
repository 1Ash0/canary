"""Validity check for policy experiments: does survival in each recorded trace match the policy run
alone on the same seed, with no model?

For every treatment episode of a deterministic policy, the same seeded history is compacted by the
same policy code with a stub reply (as in `ctxcheck survival`), and the fate at the probe is compared
with the fate the recorded trace shows. A mismatch means the harness behaved differently live than
offline: a bug, and EXP-002 says nothing is reported until it is found.

    python scripts/survival_parity.py EXP-002      # writes results/EXP-002/survival_parity.json
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from ctxcheck.canaries import build_pack
from ctxcheck.harness.loop import run
from ctxcheck.policies import make_policy
from ctxcheck.providers.scripted import ScriptedProvider
from ctxcheck.runner.episode import survival_at_probe
from ctxcheck.runner.survival import DEFAULT_POLICIES, _stub_probe_reply
from ctxcheck.schema import MessageEvent

ROOT = Path(__file__).resolve().parent.parent


def offline_fate(pack: str, seed: int, policy: str, params: dict[str, Any], limit: int) -> str:
    built = build_pack(pack, seed)
    args = {p: "x" for p in built.tools[-1].spec.input_schema["properties"]}
    events = run(built.scenario,
                 ScriptedProvider([_stub_probe_reply(built.spec.tool_name, args)]),
                 built.tools, limit_tokens=limit, policy=make_policy(policy, **params),
                 clock=lambda: "t", run_id="parity")
    probe = next(e for e in events if isinstance(e, MessageEvent)
                 and e.step == built.probe_step and e.role == "user")
    return survival_at_probe(events, built.spec.canary_id, probe.message_id)


def main() -> int:
    exp = sys.argv[1]
    text = (ROOT / "results" / exp / "episodes.jsonl").read_text(encoding="utf-8")
    rows = [json.loads(line) for line in text.splitlines() if line]
    tally: dict[str, Counter] = {}
    mismatches = []
    for r in rows:
        if r["condition"] != "treatment" or r["policy"] not in DEFAULT_POLICIES:
            continue
        expected = offline_fate(r["pack"], r["seed"], r["policy"], r["params"] or {},
                                r["limit_tokens"])
        key = f"{r['model_requested']}|{r['pack']}|{r['policy']}"
        c = tally.setdefault(key, Counter())
        c["n"] += 1
        c["agree"] += expected == r["canary_fate"]
        c["kept_offline"] += expected == "kept"
        if expected != r["canary_fate"]:
            mismatches.append({"key": key, "seed": r["seed"], "trace": r["trace_path"],
                               "offline": expected, "recorded": r["canary_fate"]})
    out = {"epistemic": "deterministic vs recorded", "exp_id": exp,
           "groups": [{"model": k.split("|")[0], "pack": k.split("|")[1],
                       "policy": k.split("|")[2], **dict(v)} for k, v in sorted(tally.items())],
           "mismatches": mismatches}
    path = ROOT / "results" / exp / "survival_parity.json"
    path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8", newline="\n")
    for g in out["groups"]:
        print(f"{g['model']:<24} {g['pack']:<11} {g['policy']:<17} agree {g['agree']}/{g['n']} "
              f"(kept offline {g['kept_offline']})")
    print(f"{len(mismatches)} mismatch(es); wrote {path.relative_to(ROOT)}")
    return 1 if mismatches else 0


if __name__ == "__main__":
    sys.exit(main())
