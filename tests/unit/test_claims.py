"""The claims checker, two-sided: passes when docs match, fails for each way they can drift."""

import json
from pathlib import Path

import pytest

from ctxcheck.claims import check_all, check_claims, check_results, resolve
from ctxcheck.runner.experiment import ExperimentPlan, estimate_tokens


def write(root: Path, rel: str, content: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def project(tmp_path: Path, claims: list[dict], doc: str = "We kept 5 of 20.") -> Path:
    write(tmp_path, "README.md", doc)
    write(tmp_path, "results/exp/summary.json", json.dumps({"cells": [{"name": "a", "k": 5}]}))
    write(tmp_path, "docs/claims.json", json.dumps(claims))
    return tmp_path


def claim(**kw) -> dict:
    base = {"id": "c1", "file": "README.md", "text": "5 of 20", "kind": "json",
            "source": "results/exp/summary.json", "path": "cells[name=a].k", "expected": 5}
    return {**base, **kw}


def test_resolve_walks_keys_indexes_and_selectors() -> None:
    data = {"cells": [{"p": "x", "q": 1, "v": 10}, {"p": "y", "q": 2, "v": 20}]}
    assert resolve(data, "cells.1.v") == 20
    assert resolve(data, "cells[p=y].v") == 20
    assert resolve(data, "cells[p=x,q=1].v") == 10
    with pytest.raises(KeyError):
        resolve(data, "cells[p=z].v")


def test_a_matching_claim_passes(tmp_path: Path) -> None:
    assert check_claims(project(tmp_path, [claim()])) == []


def test_a_changed_artifact_fails_the_claim(tmp_path: Path) -> None:
    root = project(tmp_path, [claim(expected=6)])
    problems = check_claims(root)
    assert len(problems) == 1 and "is 5" in str(problems[0]) and "says 6" in str(problems[0])


def test_a_sentence_edited_out_of_the_doc_orphans_the_claim(tmp_path: Path) -> None:
    problems = check_claims(project(tmp_path, [claim()], doc="We kept most of them."))
    assert len(problems) == 1 and "no longer appears" in str(problems[0])


def test_a_missing_source_or_path_is_a_failure_not_a_pass(tmp_path: Path) -> None:
    root = project(tmp_path, [claim(source="results/nope.json")])
    assert "does not exist" in str(check_claims(root)[0])
    root = project(tmp_path, [claim(path="cells[name=zzz].k")])
    assert "cannot read" in str(check_claims(root)[0])


def test_a_missing_doc_and_an_unknown_kind_fail(tmp_path: Path) -> None:
    assert "does not exist" in str(check_claims(project(tmp_path, [claim(file="GONE.md")]))[0])
    assert "unknown claim kind" in str(check_claims(project(tmp_path, [claim(kind="vibes")]))[0])


def test_no_registry_means_nothing_to_check(tmp_path: Path) -> None:
    assert check_claims(tmp_path) == []


def test_dryrun_claim_matches_the_planned_calls_and_tokens(tmp_path: Path) -> None:
    plan = ExperimentPlan("claim", "constraint", "head_tail", (1, 2, 3))
    tin, tout = estimate_tokens(plan)
    expected = {"calls": plan.calls_upper_bound(), "tokens_k": round((tin + tout) / 1000)}
    assert expected["calls"] == 12  # 3 seeds x 4 conditions, no summary call for head_tail
    ok = claim(kind="dryrun", pack="constraint", policy="head_tail", seeds=3, expected=expected,
               text="12 calls")
    assert check_claims(project(tmp_path, [ok], doc="at most 12 calls")) == []
    stale = {**ok, "expected": {**expected, "calls": 13}}
    assert "the plan is" in str(check_claims(project(tmp_path, [stale], doc="12 calls"))[0])


def episodes(root: Path, rel: str, source: str, summary_tag: str | None = None) -> None:
    write(root, rel, json.dumps({"key": "k", "source": source}) + "\n")
    if summary_tag:
        summary = rel.replace("episodes.jsonl", "summary.json")
        write(root, summary, json.dumps({"source": summary_tag}))


def test_recorded_rows_outside_and_simulated_rows_inside_simulated_dir_pass(
    tmp_path: Path,
) -> None:
    episodes(tmp_path, "results/EXP-001/episodes.jsonl", "recorded", "recorded")
    episodes(tmp_path, "results/simulated/EXP-001/episodes.jsonl", "simulated", "simulated")
    assert check_results(tmp_path) == []


def test_a_simulated_row_beside_real_results_fails(tmp_path: Path) -> None:
    episodes(tmp_path, "results/EXP-001/episodes.jsonl", "simulated")
    problems = check_results(tmp_path)
    assert len(problems) == 1 and "only 'recorded' may live" in str(problems[0])


def test_a_recorded_row_in_the_simulated_directory_fails(tmp_path: Path) -> None:
    episodes(tmp_path, "results/simulated/X/episodes.jsonl", "recorded")
    assert "only 'simulated' may live" in str(check_results(tmp_path)[0])


def test_a_mislabelled_summary_fails(tmp_path: Path) -> None:
    episodes(tmp_path, "results/EXP-001/episodes.jsonl", "recorded", "simulated")
    assert "tagged 'simulated'" in str(check_results(tmp_path)[0])


def test_the_real_repository_passes_its_own_checks() -> None:
    root = Path(__file__).resolve().parent.parent.parent
    assert check_all(root) == []
