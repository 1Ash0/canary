"""Export traces and results to web/public/data/ for the static site.

Run via: make export
Output: runs/<id>.json (synthetic samples and featured recorded episodes), experiments/<name>.json
(the mock, EXP-001 results and the featured pair), survival/grid.json, schema, index.json.

The site renders numbers only from these files, and every file names the artifact it came from.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ctxcheck.export import label_of, to_experiment, to_scene_input
from ctxcheck.runner.trace_io import read_trace
from ctxcheck.schema import RunStartEvent, event_json_schema, parse_event

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "web" / "public" / "data"

EXP001 = ROOT / "results" / "EXP-001"
# The landing page's story: the same seed and history under two summarizers. Chosen because the
# NVIDIA summary is complete (not cut off by the token cap) and both floor and control behave.
PAIR_SEED = 19
PAIR = [("ministral-14b-latest", "Mistral", "mistral"), ("openai/gpt-oss-20b", "NVIDIA", "nvidia")]
# How each model's row reads on the site; the numbers come from summary.json.
MODELS = [
    ("ministral-14b-latest", "Mistral", "ministral-14b-latest", True,
     "27 seeds. Its summaries almost always carried the rule through."),
    ("openai/gpt-oss-20b", "NVIDIA", "gpt-oss-20b", True,
     "27 seeds, optional third model. Many summaries were cut off by the token cap, which its "
     "reasoning eats into; cut-off summaries lost the rule more often."),
    ("openai/gpt-oss-120b", "Groq", "gpt-oss-120b", False,
     "Re-run stopped at 4 of 27 seeds. Too few to read."),
    ("gemini-3.1-flash-lite", "Gemini", "gemini-3.1-flash-lite", False,
     "Excluded: its summaries were copied transcript lines, not summaries."),
]


def write(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def finish_reasons() -> dict[str, str]:
    out: dict[str, str] = {}
    for f in (ROOT / "cassettes" / "EXP-001").rglob("*.json"):
        entry = json.loads(f.read_text(encoding="utf-8"))
        if entry["request"]["tools"] == []:
            out[entry["response"]["text"].strip()] = entry["response"]["extra"].get("finish_reason")
    return out


def exp001_results() -> dict[str, Any]:
    summary = json.loads((EXP001 / "summary.json").read_text(encoding="utf-8"))
    pilot = json.loads((ROOT / "results/EXP-001-pilot10-reanalysed/audit_tally.json")
                       .read_text(encoding="utf-8"))
    nvidia = json.loads((EXP001 / "audit_tally_nvidia.json").read_text(encoding="utf-8"))

    def cell(model: str, label: str) -> dict[str, Any]:
        c = next(x for x in summary["cells"] if x["model"] == model and x["label"] == label)
        return {"k": c["k_violated"], "n": c["n_graded"], "rate": c.get("rate"),
                "lo": c.get("wilson_lo"), "hi": c.get("wilson_hi"),
                "na": c["n_not_applicable"], "invalid": c.get("n_summary_invalid"),
                "checked": c.get("n_summary_checked"),
                "kept": (c.get("verbatim_survival") or {}).get("k_kept"),
                "kept_n": (c.get("verbatim_survival") or {}).get("n")}

    models = []
    for model, host, short, usable, note in MODELS:
        comp = next(x for x in summary["comparisons"]
                    if x["model"] == model and x["second"] == "control")
        models.append({
            "model": model, "host": host, "short": short, "usable": usable, "note": note,
            "floor": cell(model, "floor"), "control": cell(model, "control"),
            "treatment": cell(model, "treatment(llm_summary)"),
            "pairs": {"n": comp["n_pairs"], "only_treatment": comp["only_first_failed"],
                      "only_control": comp["only_second_failed"], "p": comp["p_mcnemar"],
                      "rd": comp.get("risk_difference"), "rd_lo": comp.get("rd_lo"),
                      "rd_hi": comp.get("rd_hi")},
        })
    t_pilot, t_nv = pilot["total"], nvidia["total"]
    nv = nvidia["per_model"]["openai/gpt-oss-20b"]
    return {
        "label": "recorded", "exp_id": "EXP-001", "dates": summary["dates"],
        "models": models,
        "audit": {"judged": t_pilot["behaviour_judged"] + t_nv["behaviour_judged"],
                  "followed": t_pilot["behaviour_follows_owner_call"]
                  + t_nv["behaviour_follows_owner_call"]},
        "truncation": {"truncated": nv["truncated"],
                       "truncated_present": nv["truncated_rule_present"],
                       "complete": nv["complete"], "complete_present": nv["complete_rule_present"]},
        "source": [rel(EXP001 / "summary.json"),
                   "results/EXP-001-pilot10-reanalysed/audit_tally.json",
                   rel(EXP001 / "audit_tally_nvidia.json"), "docs/experiments/EXP-001.md"],
    }


def exp001_pair(index: dict[str, list[dict[str, str]]]) -> dict[str, Any]:
    rows = [json.loads(line) for line in (EXP001 / "episodes.jsonl").read_text(encoding="utf-8")
            .splitlines() if line]
    reasons = finish_reasons()
    sides = []
    for model, host, tag in PAIR:
        row = next(r for r in rows if r["model_requested"] == model and r["seed"] == PAIR_SEED
                   and r["condition"] == "treatment")
        events = read_trace(ROOT / row["trace_path"])
        run_id = f"exp001-s{PAIR_SEED}-{tag}"
        scene = to_scene_input(events, row["trace_path"])
        scene["meta"]["run_id"] = run_id
        scene["meta"]["model"] = model
        write(OUT / "runs" / f"{run_id}.json", scene)
        index["runs"].append({"id": run_id, "label": "recorded", "path": f"runs/{run_id}.json",
                              "title": f"EXP-001 seed {PAIR_SEED}, {host} {model}"})
        planted = next(e for e in events if e.type == "canary_planted")
        rule = next(e for e in events if e.type == "message" and e.message_id == planted.message_id)
        summary = next(e for e in events if e.type == "message" and e.origin == "summary")
        probe = next(e for e in events if e.type == "message" and e.role == "user"
                     and "Please post this week's status" in e.content)
        call = next(e for e in events if e.type == "tool_call" and e.seq > probe.seq)
        text = summary.content.split("\n", 1)[1].strip()
        sides.append({
            "model": model, "host": host, "run": run_id, "rule": rule.content,
            "channel": planted.value, "probe": probe.content, "summary": text,
            "fate": row["canary_fate"], "grade": row["grade"], "call": call.args,
            "finish_reason": reasons.get(text), "trace": row["trace_path"],
        })
    return {"label": "recorded", "exp_id": "EXP-001", "seed": PAIR_SEED, "sides": sides,
            "source": rel(EXP001 / "episodes.jsonl")}


def main() -> None:
    index: dict[str, list[dict[str, str]]] = {"runs": [], "experiments": [], "survival": []}

    for path in sorted((ROOT / "runs" / "samples").glob("*.jsonl")):
        events = [parse_event(line) for line in path.read_text(encoding="utf-8").splitlines()]
        start = events[0]
        assert isinstance(start, RunStartEvent), f"{path.name} must begin with run_start"
        write(OUT / "runs" / f"{start.run_id}.json", to_scene_input(events, rel(path)))
        index["runs"].append({"id": start.run_id, "label": label_of(start.provider),
                              "path": f"runs/{start.run_id}.json",
                              "title": "Synthetic fixture, 40 steps, three facts"})

    for path in sorted((ROOT / "results" / "samples").glob("*.json")):
        result = json.loads(path.read_text(encoding="utf-8"))
        write(OUT / "experiments" / path.name, to_experiment(result, rel(path)))
        index["experiments"].append(
            {"id": path.stem, "label": result["label"], "path": f"experiments/{path.name}"})

    if (EXP001 / "summary.json").exists():  # recorded: real models, real traces
        write(OUT / "experiments" / "exp001.json", exp001_results())
        write(OUT / "experiments" / "exp001_pair.json", exp001_pair(index))
        index["experiments"] += [
            {"id": "exp001", "label": "recorded", "path": "experiments/exp001.json"},
            {"id": "exp001_pair", "label": "recorded", "path": "experiments/exp001_pair.json"}]

    grid = ROOT / "results" / "survival" / "grid.json"
    if grid.exists():  # deterministic: real policy code, no model; its tag travels in the file
        write(OUT / "survival" / "grid.json", json.loads(grid.read_text(encoding="utf-8")))
        index["survival"] = [{"id": "grid", "path": "survival/grid.json"}]

    write(OUT / "schema" / "events.schema.json", event_json_schema())
    write(OUT / "index.json", index)
    runs, experiments = len(index["runs"]), len(index["experiments"])
    print(f"exported {runs} run(s), {experiments} experiment(s) to {OUT}")


if __name__ == "__main__":
    main()
