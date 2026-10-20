"""The adapter must agree with the ledger and fates, label honestly, and carry provenance."""

from ctxcheck.export import label_of, to_experiment, to_scene_input
from ctxcheck.fates import derive_fates
from ctxcheck.ledger import replay
from ctxcheck.synthetic import generate


def words(text: str) -> int:
    return len(text.split())


def scene():
    events = generate(1, count_fn=words)
    return events, to_scene_input(events, "runs/samples/x.jsonl")


def test_synthetic_runs_are_labelled_synthetic_and_never_recorded() -> None:
    assert label_of("synthetic") == "synthetic fixture"
    assert label_of("anthropic") == "recorded"
    assert scene()[1]["meta"]["label"] == "synthetic fixture"


def test_synthetic_run_reports_no_model() -> None:
    assert scene()[1]["meta"]["model"] is None


def test_meta_carries_provenance_and_the_token_caveat() -> None:
    meta = scene()[1]["meta"]
    assert meta["source"] == "runs/samples/x.jsonl" and meta["run_id"] == "synthetic-001"
    assert "estimate" in meta["token_counts"]


def test_steps_match_the_ledger_row_for_row() -> None:
    events, out = scene()
    ledger = replay(events)
    assert [s["i"] for s in out["steps"]] == [r.step for r in ledger.rows]
    pairs = zip(out["steps"], ledger.rows, strict=True)
    assert all(s["layers"] == dict(r.layers) for s, r in pairs)
    assert out["meta"]["limit_tokens"] == ledger.limit_tokens


def test_compaction_points_at_the_row_after_the_drop() -> None:
    events, out = scene()
    ledger = replay(events)
    assert out["compaction"]["at_step"] == 31
    assert out["compaction"]["after"] == dict(ledger.rows[31].layers)  # step 32


def test_canaries_carry_planted_step_and_derived_fate() -> None:
    events, out = scene()
    fates = derive_fates(events)
    planted = [(c["id"], c["planted_step"]) for c in out["canaries"]]
    assert planted == [("C1", 3), ("C2", 9), ("C3", 14)]
    assert {c["id"]: c["fate"] for c in out["canaries"]} == fates
    assert all(c["after_text"] is None for c in out["canaries"])


def test_every_canary_fate_is_kept_or_gone_only() -> None:
    assert {c["fate"] for c in scene()[1]["canaries"]} <= {"kept", "gone"}


def test_experiment_passes_through_with_its_label_and_a_source() -> None:
    result = {"label": "mock data", "epistemic": "simulated", "cells": {}}
    out = to_experiment(result, "results/samples/m.json")
    assert out["label"] == "mock data" and out["epistemic"] == "simulated"
    assert out["source"] == "results/samples/m.json"
    assert "source" not in result  # input not mutated


def test_run_without_compaction_has_no_compaction_block() -> None:
    events = generate(1, count_fn=words, compact_after=999)
    assert to_scene_input(events, "s")["compaction"] is None
