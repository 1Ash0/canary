"""Check that numbers cited in docs match the artifacts they come from.

The rule is no number without an artifact. `docs/claims.json` registers each checkable claim: the
exact `text` that must appear in `file`, and where its value comes from. Two kinds:

  json    a value at `path` in a JSON file under results/ must equal `expected`
  dryrun  an experiment plan's call and token estimate (computed, not stored) must match

A claim fails if the text is gone from the doc (orphaned), the source is missing, or the value
differs. The results themselves are checked too: simulated rows may exist only under
`results/simulated/` and recorded rows only outside it, so a simulated number can never sit beside a
measured one.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ctxcheck.runner.experiment import ExperimentPlan, estimate_tokens


@dataclass(frozen=True)
class Problem:
    where: str
    message: str

    def __str__(self) -> str:
        return f"{self.where}: {self.message}"


def resolve(data: Any, path: str) -> Any:
    """Walk `a.b[k=v,k2=v2].c`: dict keys, list indexes, or a selector for the first match."""
    for token in re.findall(r"\[[^\]]*\]|[^.\[\]]+", path):
        if token.startswith("["):
            wanted = dict(pair.split("=", 1) for pair in token[1:-1].split(","))
            matches = [item for item in data
                       if all(str(item.get(k)) == v for k, v in wanted.items())]
            if not matches:
                raise KeyError(f"no list item matches {token}")
            data = matches[0]
        elif isinstance(data, list):
            data = data[int(token)]
        else:
            data = data[token]
    return data


def _check_one(root: Path, claim: dict[str, Any]) -> list[Problem]:
    cid = claim.get("id", "?")
    doc = root / claim["file"]
    if not doc.exists():
        return [Problem(cid, f"{claim['file']} does not exist")]
    if claim["text"] not in doc.read_text(encoding="utf-8"):
        return [Problem(cid, f"text no longer appears in {claim['file']}: {claim['text']!r}")]

    if claim["kind"] == "json":
        source = root / claim["source"]
        if not source.exists():
            return [Problem(cid, f"source {claim['source']} does not exist")]
        try:
            actual = resolve(json.loads(source.read_text(encoding="utf-8")), claim["path"])
        except (KeyError, IndexError, ValueError) as e:
            return [Problem(cid, f"cannot read {claim['path']} in {claim['source']}: {e}")]
        if actual != claim["expected"]:
            return [Problem(cid, f"{claim['source']} {claim['path']} is {actual!r}, "
                                 f"the doc says {claim['expected']!r}")]
        return []

    if claim["kind"] == "dryrun":
        plan = ExperimentPlan("claim", claim["pack"], claim["policy"],
                              tuple(range(1, claim["seeds"] + 1)))
        tin, tout = estimate_tokens(plan)
        actual = {"calls": plan.calls_upper_bound(), "tokens_k": round((tin + tout) / 1000)}
        if actual != claim["expected"]:
            return [Problem(cid, f"the plan is {actual}, the doc says {claim['expected']}")]
        return []

    return [Problem(cid, f"unknown claim kind {claim['kind']!r}")]


def check_claims(root: Path) -> list[Problem]:
    registry = root / "docs" / "claims.json"
    if not registry.exists():
        return []
    problems: list[Problem] = []
    for claim in json.loads(registry.read_text(encoding="utf-8")):
        problems += _check_one(root, claim)
    return problems


def check_results(root: Path) -> list[Problem]:
    problems: list[Problem] = []
    results = root / "results"
    for episodes in sorted(results.rglob("episodes.jsonl")):
        rel = episodes.relative_to(root).as_posix()
        in_simulated = "simulated" in episodes.relative_to(results).parts
        want = "simulated" if in_simulated else "recorded"
        rows = [json.loads(line) for line in episodes.read_text(encoding="utf-8").splitlines()
                if line]
        bad = sorted({r.get("source") for r in rows} - {want})
        if bad:
            problems.append(Problem(rel, f"rows with source {bad} where only {want!r} may live"))
        summary = episodes.with_name("summary.json")
        if summary.exists():
            tag = json.loads(summary.read_text(encoding="utf-8")).get("source")
            if tag != want:
                problems.append(Problem(summary.relative_to(root).as_posix(),
                                        f"summary is tagged {tag!r}, expected {want!r}"))
    return problems


def check_all(root: Path) -> list[Problem]:
    return [*check_claims(root), *check_results(root)]
