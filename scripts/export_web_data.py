"""Export runs/samples/*.jsonl and results/samples/*.json to web/public/data/ for the static site.

Run via: make export
Output: runs/<run_id>.json, experiments/<name>.json, schema/events.schema.json, index.json
"""

from __future__ import annotations

import json
from pathlib import Path

from ctxcheck.export import label_of, to_experiment, to_scene_input
from ctxcheck.schema import RunStartEvent, event_json_schema, parse_event

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "web" / "public" / "data"


def write(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    index: dict[str, list[dict[str, str]]] = {"runs": [], "experiments": []}

    for path in sorted((ROOT / "runs" / "samples").glob("*.jsonl")):
        events = [parse_event(line) for line in path.read_text(encoding="utf-8").splitlines()]
        start = events[0]
        assert isinstance(start, RunStartEvent), f"{path.name} must begin with run_start"
        rel = path.relative_to(ROOT).as_posix()
        write(OUT / "runs" / f"{start.run_id}.json", to_scene_input(events, rel))
        index["runs"].append(
            {
                "id": start.run_id,
                "label": label_of(start.provider),
                "path": f"runs/{start.run_id}.json",
            }
        )

    for path in sorted((ROOT / "results" / "samples").glob("*.json")):
        result = json.loads(path.read_text(encoding="utf-8"))
        rel = path.relative_to(ROOT).as_posix()
        write(OUT / "experiments" / path.name, to_experiment(result, rel))
        index["experiments"].append(
            {"id": path.stem, "label": result["label"], "path": f"experiments/{path.name}"}
        )

    write(OUT / "schema" / "events.schema.json", event_json_schema())
    write(OUT / "index.json", index)
    runs, experiments = len(index["runs"]), len(index["experiments"])
    print(f"exported {runs} run(s), {experiments} experiment(s) to {OUT}")


if __name__ == "__main__":
    main()
