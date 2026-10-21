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
from ctxcheck.lab import lab_history, parity_cases
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


TAGS = {"ministral-14b-latest": "mistral", "openai/gpt-oss-20b": "nvidia",
        "openai/gpt-oss-120b": "groq", "gemini-3.1-flash-lite": "gemini"}


def read_rows(exp_dir: Path) -> list[dict[str, Any]]:
    text = (exp_dir / "episodes.jsonl").read_text(encoding="utf-8")
    return [json.loads(line) for line in text.splitlines() if line]


def run_id_of(prefix: str, r: dict[str, Any], detail: bool) -> str:
    """exp001-s19-nvidia; with several policies or packs, exp002-s5-nvidia-head_tail-constraint."""
    base = f"{prefix}-s{r['seed']}-{TAGS[r['model_requested']]}"
    return f"{base}-{r['policy']}-{r['pack']}" if detail else base


def export_episode_runs(exp_dir: Path, prefix: str, models: list[str],
                        index: dict[str, list[dict[str, str]]], detail: bool = False) -> int:
    """Every treatment episode of these models as a recorder run, so the results page can link a
    seed dot to the exact episode. Runs beyond the first experiment are written compact."""
    n = 0
    for r in read_rows(exp_dir):
        if r["model_requested"] not in models or r["condition"] != "treatment":
            continue
        run_id = run_id_of(prefix, r, detail)
        scene = to_scene_input(read_trace(ROOT / r["trace_path"]), r["trace_path"])
        scene["meta"].update(run_id=run_id, model=r["model_requested"], exp=exp_dir.name)
        write(OUT / "runs" / f"{run_id}.json", scene, compact=prefix != "exp001")
        if not any(x["id"] == run_id for x in index["runs"]):
            title = f"{exp_dir.name} seed {r['seed']}, {r['model_requested']}"
            if detail:
                title += f", {r['policy']}, {r['pack']} pack"
            index["runs"].append({"id": run_id, "label": "recorded", "path": f"runs/{run_id}.json",
                                  "title": title, "group": exp_dir.name})
        n += 1
    return n


def experiment_blocks(exp_dir: Path, prefix: str, spec: list[dict[str, Any]],
                      detail: bool = False) -> list[dict[str, Any]]:
    """One block per model and pack: a row per condition with its Wilson interval and one mark per
    seed, and the comparisons the summary lists for that block (primary first)."""
    summary = json.loads((exp_dir / "summary.json").read_text(encoding="utf-8"))
    rows = read_rows(exp_dir)
    blocks = []
    for b in spec:
        model, pack = b["model"], b.get("pack", "constraint")
        out_rows = []
        for label, name in b["rows"]:
            c = next((x for x in summary["cells"] if x["model"] == model
                      and x.get("pack", pack) == pack and x["label"] == label), None)
            if c is None:
                continue
            mine = sorted((r for r in rows if r["model_requested"] == model and r["pack"] == pack
                           and label_of_row(r) == label), key=lambda r: r["seed"])
            out_rows.append({
                "label": label, "name": name, "k": c["k_violated"], "n": c["n_graded"],
                "rate": c.get("rate"), "lo": c.get("wilson_lo"), "hi": c.get("wilson_hi"),
                "na": c["n_not_applicable"], "truncated": c.get("n_summary_truncated"),
                "truncation_known": c.get("n_truncation_known"),
                "seeds": [{"seed": r["seed"], "grade": r["grade"], "fate": r["canary_fate"],
                           "evidence": r["evidence"], "truncated": r.get("summary_truncated"),
                           "run": run_id_of(prefix, r, detail)
                           if r["condition"] == "treatment" else None} for r in mine]})
        names = dict(b["rows"])
        comps = [{"first": names.get(c["first"], c["first"]),
                  "second": names.get(c["second"], c["second"]), "role": c.get("role", "primary"),
                  "n": c["n_pairs"], "only_first": c["only_first_failed"],
                  "only_second": c["only_second_failed"], "p": c["p_mcnemar"], "q": c["q_bh"],
                  "rd": c.get("risk_difference"), "rd_lo": c.get("rd_lo"), "rd_hi": c.get("rd_hi")}
                 for c in summary["comparisons"]
                 if c["model"] == model and c.get("pack", pack) == pack
                 and c["first"] in names and c["second"] in names]
        comps.sort(key=lambda c: c["role"] != "primary")
        blocks.append({"model": model, "pack": pack, "host": b["host"], "note": b.get("note", ""),
                       "rows": out_rows, "comparisons": comps})
    return blocks


def label_of_row(r: dict[str, Any]) -> str:
    return r["condition"] if r.get("policy") is None else f"{r['condition']}({r['policy']})"


EXP001B = ROOT / "results" / "EXP-001b"
EXP002 = ROOT / "results" / "EXP-002"
POLICY_ROWS = [("floor", "never told"), ("control", "full context"),
               ("treatment(recency_truncate)", "drop oldest"),
               ("treatment(head_tail)", "keep head and tail"),
               ("treatment(observation_mask)", "mask tool output"),
               ("treatment(llm_summary)", "model summary")]


def exp001b_results() -> dict[str, Any]:
    summary = json.loads((EXP001B / "summary.json").read_text(encoding="utf-8"))
    spec = [{"model": "openai/gpt-oss-20b", "host": "NVIDIA",
             "rows": [("control", "control"), ("length_matched(llm_summary)", "length-matched"),
                      ("treatment(llm_summary)", "treatment")],
             "note": "Same 27 seeds as EXP-001, reasoning kept short on the summary call."}]
    tally = json.loads((EXP001B / "audit_tally.json").read_text(encoding="utf-8"))["total"]
    return {"label": "recorded", "exp_id": "EXP-001b", "dates": summary["dates"],
            "blocks": experiment_blocks(EXP001B, "exp001b", spec),
            "audit": {"followed": tally["behaviour_follows_owner_call"],
                      "judged": tally["behaviour_judged"],
                      "agree": tally["machine_agrees_rule_present"],
                      "summaries": tally["summaries_judged"]},
            "source": [rel(EXP001B / "summary.json"), rel(EXP001B / "audit_tally.json"),
                       "docs/experiments/EXP-001b.md"]}


def exp002_results() -> dict[str, Any]:
    summary = json.loads((EXP002 / "summary.json").read_text(encoding="utf-8"))
    spec = [{"model": "ministral-14b-latest", "pack": "constraint", "host": "Mistral",
             "rows": POLICY_ROWS},
            {"model": "ministral-14b-latest", "pack": "identifier", "host": "Mistral",
             "rows": POLICY_ROWS},
            {"model": "openai/gpt-oss-20b", "pack": "constraint", "host": "NVIDIA",
             "rows": POLICY_ROWS}]
    blocks = [b for b in experiment_blocks(EXP002, "exp002", spec, detail=True) if b["rows"]]
    return {"label": "recorded", "exp_id": "EXP-002", "dates": summary["dates"],
            "limit_tokens": summary["cells"][0]["limit_tokens"], "blocks": blocks,
            "source": [rel(EXP002 / "summary.json"), "docs/experiments/EXP-002.md"]}


def write(path: Path, data: object, compact: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, separators=(",", ":")) if compact else json.dumps(data, indent=2)
    path.write_text(text + "\n", encoding="utf-8", newline="\n")


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

    rows = [json.loads(line) for line in (EXP001 / "episodes.jsonl").read_text(encoding="utf-8")
            .splitlines() if line]

    def seeds_of(model: str, condition: str, exp: str = "exp001") -> list[dict[str, Any]]:
        mine = sorted((r for r in rows if r["model_requested"] == model
                       and r["condition"] == condition), key=lambda r: r["seed"])
        return [{"seed": r["seed"], "grade": r["grade"], "fate": r["canary_fate"],
                 "evidence": r["evidence"], "truncated": r.get("summary_truncated"),
                 "run": f"{exp}-s{r['seed']}-{TAGS[model]}" if condition == "treatment" else None}
                for r in mine]

    models = []
    for model, host, short, usable, note in MODELS:
        comp = next(x for x in summary["comparisons"]
                    if x["model"] == model and x["second"] == "control")
        models.append({
            "model": model, "host": host, "short": short, "usable": usable, "note": note,
            "floor": cell(model, "floor"), "control": cell(model, "control"),
            "treatment": cell(model, "treatment(llm_summary)"),
            "seeds": {"control": seeds_of(model, "control"),
                      "treatment": seeds_of(model, "treatment")} if usable else None,
            "pairs": {"n": comp["n_pairs"], "only_treatment": comp["only_first_failed"],
                      "only_control": comp["only_second_failed"], "p": comp["p_mcnemar"],
                      "rd": comp.get("risk_difference"), "rd_lo": comp.get("rd_lo"),
                      "rd_hi": comp.get("rd_hi")},
        })
    t_pilot, t_nv = pilot["total"], nvidia["total"]
    nv = nvidia["per_model"]["openai/gpt-oss-20b"]
    spec = [{"model": model, "host": host, "note": note,
             "rows": [("control", "control"), ("treatment(llm_summary)", "treatment")]}
            for model, host, _, usable, note in MODELS if usable]
    return {
        "label": "recorded", "exp_id": "EXP-001", "dates": summary["dates"],
        "models": models, "blocks": experiment_blocks(EXP001, "exp001", spec),
        "other": [{"host": host, "model": model, "note": note}
                  for model, host, _, usable, note in MODELS if not usable],
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


def lab_summaries(seeds: range) -> dict[str, Any]:
    """Recorded summaries for the lab's summary mode: per seed and summarizer, the text, whether it
    still named the rule, what the agent then did. From EXP-002's channel-rule summary episodes, the
    same episodes the Lab's "what real models did" line links to (one experiment, one summary)."""
    reasons = finish_reasons()
    sources = [("mistral", "ministral-14b-latest", ["EXP-002"]),
               ("nvidia", "openai/gpt-oss-20b", ["EXP-002"])]
    out: dict[str, Any] = {}
    for tag, model, exps in sources:
        for exp in exps:
            path = ROOT / "results" / exp / "episodes.jsonl"
            if not path.exists():
                continue
            text_rows = path.read_text(encoding="utf-8").splitlines()
            rows = [json.loads(line) for line in text_rows if line]
            for seed in seeds:
                key = f"{seed}"
                if tag in out.get(key, {}):
                    continue
                row = next((r for r in rows if r["model_requested"] == model
                            and r["seed"] == seed and r["condition"] == "treatment"
                            and r.get("policy", "llm_summary") == "llm_summary"
                            and r.get("pack", "constraint") == "constraint"
                            and r["summary_valid"] is not None), None)
                if row is None:
                    continue
                events = read_trace(ROOT / row["trace_path"])
                summ = next(e for e in events if e.type == "message" and e.origin == "summary")
                # gpt-oss sometimes names the tool "post_status<|channel|>commentary"
                call = next((e for e in events if e.type == "tool_call"
                             and e.name.startswith("post_status") and e.seq > summ.seq), None)
                text = summ.content.split("\n", 1)[1].strip()
                out.setdefault(key, {})[tag] = {
                    "model": model, "exp": exp, "text": text, "tokens": summ.tokens_est,
                    "fate": row["canary_fate"], "grade": row["grade"],
                    "chosen": call.args.get("channel") if call else None,
                    "truncated": row.get("summary_truncated", reasons.get(text) == "length"),
                    "trace": row["trace_path"]}
    return {"epistemic": "recorded", "seeds": out}


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
        export_episode_runs(EXP001, "exp001", ["ministral-14b-latest", "openai/gpt-oss-20b"], index)
        index["experiments"] += [
            {"id": "exp001", "label": "recorded", "path": "experiments/exp001.json"},
            {"id": "exp001_pair", "label": "recorded", "path": "experiments/exp001_pair.json"}]
    if (EXP001B / "summary.json").exists():
        write(OUT / "experiments" / "exp001b.json", exp001b_results())
        export_episode_runs(EXP001B, "exp001b", ["openai/gpt-oss-20b"], index)
        index["experiments"].append(
            {"id": "exp001b", "label": "recorded", "path": "experiments/exp001b.json"})
    if (EXP002 / "summary.json").exists():
        write(OUT / "experiments" / "exp002.json", exp002_results())
        export_episode_runs(EXP002, "exp002", list(TAGS), index, detail=True)
        index["experiments"].append(
            {"id": "exp002", "label": "recorded", "path": "experiments/exp002.json"})

    # the lab: real scripted histories, and parity cases that pin the JS policies to the Python
    write(OUT / "lab" / "constraint.json",
          {"epistemic": "simulated",
           "description": "Real seeded histories with exact token counts; "
           "the browser runs a JS port of the Python policies, checked against them in the design "
           "tests.", "seeds": [lab_history(s) for s in range(1, 28)]})
    write(OUT / "lab" / "summaries.json", lab_summaries(range(1, 28)))
    write(ROOT / "design" / "tests" / "fixtures" / "lab-parity.json",
          parity_cases(range(1, 6), (0, 1, 5, 9, 14, 17), (900, 1300, 1800, 2400, 3000, 3600)))

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
