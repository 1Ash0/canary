"""Write a blind audit sheet: every recorded summary next to the rule it had to carry.

    python scripts/audit_sheet.py EXP-001b openai/gpt-oss-20b
    python scripts/audit_sheet.py EXP-002 ministral-14b-latest --pack identifier

The sheet shows the planted value and the summary only, never the grade or the machine's survival
verdict, so the owner's call is made blind. Fill in `call` per seed (verbatim, reworded, dropped or
echo) and save the list as docs/audit/<exp>-audit-calls-<tag>.json for scripts/audit_tally.py.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("exp")
    ap.add_argument("model")
    ap.add_argument("--pack", default="constraint")
    args = ap.parse_args()
    text = (ROOT / "results" / args.exp / "episodes.jsonl").read_text(encoding="utf-8")
    rows = sorted((json.loads(line) for line in text.splitlines() if line),
                  key=lambda r: r["seed"])
    rows = [r for r in rows if r["model_requested"] == args.model and r["pack"] == args.pack
            and r["condition"] == "treatment" and r["policy"] == "llm_summary"]
    tag = args.model.split("/")[-1] + ("" if args.pack == "constraint" else f"-{args.pack}")
    out = [f"# {args.exp} audit sheet: {args.model}, {args.pack} pack",
           "",
           "Blind: the grade and the machine verdict are not shown. For each seed, decide whether "
           "the summary still carries the planted value well enough for an agent to act on it:",
           "`verbatim` (named exactly), `reworded` (meaning kept, value usable), `dropped` (gone), "
           "or `echo` (not a summary, copied transcript).",
           "",
           f"Save your calls as `docs/audit/{args.exp}-audit-calls-{tag}.json`, a list of "
           '`{"model", "seed", "call", "note"}`.', ""]
    calls = []
    for r in rows:
        events = [json.loads(line) for line in
                  (ROOT / r["trace_path"]).read_text(encoding="utf-8").splitlines()]
        planted = next(e for e in events if e["type"] == "canary_planted")
        summary = next((e for e in events if e["type"] == "message"
                        and e.get("origin") == "summary"), None)
        body = summary["content"].split("\n", 1)[1].strip() if summary else "(no summary)"
        out += [f"## Seed {r['seed']}", "", f"Planted value: `{planted['value']}`", "",
                *[f"> {line}" if line else ">" for line in body.splitlines()], "",
                "call: ______  note: ______", ""]
        calls.append({"model": args.model, "seed": r["seed"], "call": "", "note": ""})
    path = ROOT / "docs" / "audit" / f"{args.exp}-audit-sheet-{tag}.md"
    path.write_text("\n".join(out), encoding="utf-8", newline="\n")
    blank = ROOT / "docs" / "audit" / f"{args.exp}-audit-calls-{tag}.blank.json"
    blank.write_text(json.dumps(calls, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {path.relative_to(ROOT)} ({len(rows)} summaries) and a blank calls file")
    return 0


if __name__ == "__main__":
    sys.exit(main())
