"""Write an experiment's Results section from its summary.json, registering every number as a claim.

    python scripts/write_results.py EXP-001b --title "Results" [--verdict-file notes.md]

The section is replaced in place (between its heading and the next `## ` heading), so rerunning
after new episodes keeps the doc and docs/claims.json in step with the data. Prose that interprets
the numbers is passed in with --notes and may only use {placeholders} that this script fills from
the summary, so no number in the section is typed by hand.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TL = "treatment"


def build(exp: str, notes: str) -> tuple[str, list[dict]]:
    src = f"results/{exp}/summary.json"
    s = json.loads((ROOT / src).read_text(encoding="utf-8"))
    doc = f"docs/experiments/{exp}.md"
    claims: list[dict] = []

    def claim(cid: str, text: str, path: str, value) -> None:
        claims.append({"id": f"{exp.lower()}-{cid}", "file": doc, "text": text, "kind": "json",
                       "source": src, "path": path, "expected": value})

    lines = ["| Model | Condition | Broke the rule | 95% interval | No summary | Cut off "
             "| Invalid summary |", "|---|---|---|---|---|---|---|"]
    fill: dict[str, str] = {}
    for c in s["cells"]:
        if c.get("rate") is None:
            continue
        p = f"cells[model={c['model']},label={c['label']},limit_tokens={c['limit_tokens']}]"
        trunc = (f"{c['n_summary_truncated']} of {c['n_truncation_known']}"
                 if c.get("n_truncation_known") else "–")
        inval = (f"{c['n_summary_invalid']} of {c['n_summary_checked']}"
                 if c.get("n_summary_checked") else "–")
        row = (f"| `{c['model']}` | {c['label']} | {c['k_violated']}/{c['n_graded']} | "
               f"{c['wilson_lo']:.0%}–{c['wilson_hi']:.0%} | {c['n_not_applicable']} | "
               f"{trunc} | {inval} |")
        lines.append(row)
        key = f"{c['model'].split('/')[-1]}|{c['label']}"
        for f, v in (("k_violated", c["k_violated"]), ("n_graded", c["n_graded"]),
                     ("n_not_applicable", c["n_not_applicable"])):
            claim(f"{key}-{f}", row, f"{p}.{f}", v)
        if c.get("n_truncation_known"):
            claim(f"{key}-trunc", row, f"{p}.n_summary_truncated", c["n_summary_truncated"])
        fill[f"{key}|rate"] = f"{c['k_violated']} of {c['n_graded']}"
        if c.get("fate_matches_grade"):
            fm = c["fate_matches_grade"]
            text = f"{fm['k']} of {fm['n']}"
            fill[f"{key}|fate"] = text
        if c.get("verbatim_survival"):
            v = c["verbatim_survival"]
            fill[f"{key}|kept"] = f"{v['k_kept']} of {v['n']}"
    comps = []
    for c in s["comparisons"]:
        if c.get("risk_difference") is None:
            continue
        p = f"comparisons[model={c['model']},first={c['first']},second={c['second']}]"
        text = (f"`{c['model']}`, {c['first']} vs {c['second']}: {c['only_first_failed']} versus "
                f"{c['only_second_failed']} discordant pairs of {c['n_pairs']}, risk difference "
                f"{c['risk_difference']:+.0%} (95% bootstrap {c['rd_lo']:+.0%} to "
                f"{c['rd_hi']:+.0%}), "
                f"exact McNemar p = {c['p_mcnemar']:.2g}, BH q = {c['q_bh']:.2g}")
        comps.append(f"- {text}.")
        key = f"{c['model'].split('/')[-1]}|{c['first']}|{c['second']}"
        for f in ("only_first_failed", "only_second_failed", "n_pairs", "p_mcnemar", "q_bh",
                  "risk_difference", "rd_lo", "rd_hi"):
            claim(f"{key}-{f}", text, f"{p}.{f}", c[f])
    def slot(key: str) -> str:
        for a, b in (("|", "_"), ("(", ""), (")", ""), ("-", "_"), (".", "_")):
            key = key.replace(a, b)
        return key

    body = notes.format(**{slot(k): v for k, v in fill.items()}) if notes else ""
    section = (f"## Results\n\nRecorded {', '.join(s['dates'])}; source `{src}` (regenerate with "
               f"`ctxcheck report results/{exp}`, then `python scripts/write_results.py {exp}`). "
               f"{s['n_episodes']} episodes. Epistemic tag: `{s['source']}`. Every number below is "
               f"generated from the summary and checked by `scripts/check_claims.py`.\n\n"
               + "\n".join(lines) + "\n\n### Comparisons\n" + "\n".join(comps) + "\n\n"
               + body + "\n")
    return section, claims


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("exp")
    ap.add_argument("--notes", default="", help="file with interpretation prose ({placeholders})")
    args = ap.parse_args()
    notes = (ROOT / args.notes).read_text(encoding="utf-8") if args.notes else ""
    section, claims = build(args.exp, notes)
    doc = ROOT / f"docs/experiments/{args.exp}.md"
    text = doc.read_text(encoding="utf-8")
    start = text.index("## Results")
    nxt = text.find("\n## ", start + 5)
    text = text[:start] + section + (text[nxt + 1:] if nxt != -1 else "")
    doc.write_text(text, encoding="utf-8", newline="\n")
    reg = ROOT / "docs/claims.json"
    old = [c for c in json.loads(reg.read_text(encoding="utf-8"))
           if not c["id"].startswith(f"{args.exp.lower()}-")]
    reg.write_text(json.dumps(old + claims, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"{len(claims)} claims for {args.exp}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
