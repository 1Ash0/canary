"""Episodes and the experiment matrix, end to end with the simulated agent (never measured)."""

import json
from pathlib import Path

import pytest

from ctxcheck.harness.budget import BudgetExceeded
from ctxcheck.providers.cassette import CassetteMiss, CassetteProvider
from ctxcheck.providers.simulated import SimulatedAgent
from ctxcheck.runner.analysis import analyse
from ctxcheck.runner.episode import EpisodeSpec, run_episode
from ctxcheck.runner.experiment import ExperimentPlan, read_rows, run_experiment
from ctxcheck.runner.trace_io import read_trace


def plan(pack="constraint", policy="llm_summary", seeds=(1, 2, 3), **kw) -> ExperimentPlan:
    return ExperimentPlan("EXP-T", pack, policy, tuple(seeds), **kw)


def go(tmp_path: Path, p: ExperimentPlan, agent=None, **kw):
    return run_experiment(p, agent or SimulatedAgent(seed=1), provider_name="sim",
                          model="sim", out_dir=tmp_path / "res", runs_dir=tmp_path / "runs",
                          source="simulated", **kw)


def spec(condition: str, **kw) -> EpisodeSpec:
    has_policy = condition in ("treatment", "length_matched")
    policy = kw.pop("policy", "llm_summary" if has_policy else None)
    return EpisodeSpec("EXP-T", "constraint", condition, 1, 0, policy=policy, **kw)


def episode(tmp_path: Path, condition: str, agent=None, matched=None, **kw):
    return run_episode(spec(condition, **kw), agent or SimulatedAgent(p_follow=1.0, seed=1),
                       provider_name="sim", model="sim", runs_dir=tmp_path, matched_tokens=matched,
                       source="simulated")


def test_a_treatment_policy_is_required_only_for_the_treatment() -> None:
    with pytest.raises(ValueError, match="policy"):
        EpisodeSpec("E", "constraint", "treatment", 1, 0)
    with pytest.raises(ValueError, match="policy"):
        EpisodeSpec("E", "constraint", "length_matched", 1, 0)
    with pytest.raises(ValueError, match="policy"):
        EpisodeSpec("E", "constraint", "control", 1, 0, policy="head_tail")
    with pytest.raises(ValueError, match="unknown condition"):
        EpisodeSpec("E", "constraint", "typo", 1, 0)


def test_cell_keys_are_stable_and_distinct() -> None:
    assert spec("control").key == spec("control").key
    assert len({spec(c).key for c in ("floor", "control", "treatment")}) == 3
    assert spec("control").key != EpisodeSpec("EXP-T", "constraint", "control", 2, 0).key


def test_control_does_not_compact_and_a_following_agent_respects_the_rule(tmp_path) -> None:
    row = episode(tmp_path, "control")
    assert not row.compacted and row.grade == "respected" and row.model_calls == 1
    assert row.canary_fate is None and row.source == "simulated"


def test_floor_cannot_know_the_rule_so_it_only_guesses(tmp_path) -> None:
    rows = [run_episode(EpisodeSpec("EXP-T", "constraint", "floor", s, 0), SimulatedAgent(seed=3),
                        provider_name="sim", model="sim", runs_dir=tmp_path, source="simulated")
            for s in range(1, 21)]
    violated = sum(r.grade == "violated" for r in rows)
    assert 10 <= violated <= 20  # one real channel in four: about 75% wrong by chance, never 0%


def test_treatment_compacts_and_records_the_summary_call_and_the_fate(tmp_path) -> None:
    row = episode(tmp_path, "treatment", SimulatedAgent(p_follow=1.0, p_keep_in_summary=1.0))
    assert row.compacted and row.summary_calls == 1 and row.model_calls == 1
    assert row.canary_fate == "kept" and row.grade == "respected"
    assert row.prompt_version == "v1" and row.tokens_after < row.tokens_before


def test_a_summary_that_loses_the_rule_makes_the_agent_guess(tmp_path) -> None:
    agent = SimulatedAgent(p_follow=1.0, p_keep_in_summary=0.0)
    rows = [run_episode(EpisodeSpec("EXP-T", "constraint", "treatment", s, 0,
                                    policy="llm_summary"), agent, provider_name="sim",
                        model="sim", runs_dir=tmp_path, source="simulated")
            for s in range(1, 13)]
    assert all(r.canary_fate == "gone" for r in rows)
    assert sum(r.grade == "violated" for r in rows) >= 5


def test_a_deterministic_policy_needs_no_summary_call(tmp_path) -> None:
    row = episode(tmp_path, "treatment", policy="recency_truncate")
    assert row.compacted and row.summary_calls == 0 and row.canary_fate == "gone"


def test_head_tail_keeps_the_early_canary_that_recency_loses(tmp_path) -> None:
    ht = episode(tmp_path, "treatment", policy="head_tail",
                 policy_options=(("head_ratio", 0.5),))
    assert ht.canary_fate == "kept" and ht.grade == "respected"


def test_length_matched_is_not_compacted_but_is_as_short_as_the_treatment(tmp_path) -> None:
    t = episode(tmp_path, "treatment", policy="recency_truncate")
    lm = episode(tmp_path, "length_matched", policy="recency_truncate", matched=t.window_at_probe)
    assert not lm.compacted and lm.window_at_probe <= t.window_at_probe
    assert t.window_at_probe - lm.window_at_probe < 700  # within about one filler turn
    assert lm.grade == "respected"  # the canary is intact in a window of the same size


def test_length_matched_refuses_to_run_without_a_target(tmp_path) -> None:
    with pytest.raises(ValueError, match="treatment"):
        episode(tmp_path, "length_matched")


def test_the_trace_is_valid_and_ends_with_the_probe_then_run_end(tmp_path) -> None:
    row = episode(tmp_path, "treatment", policy="recency_truncate")
    events = read_trace(Path(row.trace_path))
    assert [e.type for e in events[-2:]] == ["canary_probe", "run_end"]
    assert [e.seq for e in events] == list(range(len(events)))
    assert events[-2].grade == row.grade and events[0].params["scripted_turns"] > 0


# --- the matrix ---------------------------------------------------------------------------------

def test_the_matrix_runs_every_condition_for_every_seed(tmp_path) -> None:
    report = go(tmp_path, plan(seeds=(1, 2)))
    assert report.ran == 8 and report.stopped is None
    rows = read_rows(tmp_path / "res" / "episodes.jsonl")
    assert sorted({r["condition"] for r in rows}) == ["control", "floor", "length_matched",
                                                      "treatment"]
    assert {r["source"] for r in rows} == {"simulated"}


def test_calls_upper_bound_counts_the_summary() -> None:
    assert plan(seeds=(1, 2, 3)).calls_upper_bound() == 15  # 3 seeds x (4 probes + 1 summary)
    assert plan(policy="head_tail", seeds=(1, 2, 3)).calls_upper_bound() == 12


def test_a_rerun_skips_finished_cells_and_adds_nothing(tmp_path) -> None:
    p = plan(seeds=(1, 2))
    go(tmp_path, p)
    before = (tmp_path / "res" / "episodes.jsonl").read_text(encoding="utf-8")
    again = go(tmp_path, p)
    assert (again.ran, again.skipped) == (0, 8)
    assert (tmp_path / "res" / "episodes.jsonl").read_text(encoding="utf-8") == before


def test_resume_after_a_crash_finishes_only_what_is_missing(tmp_path) -> None:
    p = plan(seeds=(1, 2))
    go(tmp_path, p)
    path = tmp_path / "res" / "episodes.jsonl"
    lines = path.read_text(encoding="utf-8").splitlines()
    path.write_text("\n".join(lines[:5]) + "\n", encoding="utf-8")  # as if killed after 5 episodes
    report = go(tmp_path, p)
    assert (report.ran, report.skipped) == (3, 5)
    assert len(read_rows(path)) == 8 and len({r["key"] for r in read_rows(path)}) == 8


def test_a_budget_stop_keeps_the_partial_results(tmp_path) -> None:
    class StopAfter:
        def __init__(self, n: int) -> None:
            self.n, self.inner = n, SimulatedAgent(seed=1)

        def complete(self, *a, **k):
            if self.n == 0:
                raise BudgetExceeded("run request cap 3 reached")
            self.n -= 1
            return self.inner.complete(*a, **k)

    report = go(tmp_path, plan(seeds=(1, 2)), agent=StopAfter(3))
    # floor and control took one call each; the treatment needs two and was stopped on its second,
    # so it leaves no half-recorded row behind
    assert report.stopped and "budget" in report.stopped and report.ran == 2
    assert len(read_rows(tmp_path / "res" / "episodes.jsonl")) == 2


def test_replay_mode_reports_missing_cassettes_instead_of_calling_anything(tmp_path) -> None:
    cassette = CassetteProvider(tmp_path / "c", "replay", provider_name="sim", model="sim")
    report = go(tmp_path, plan(seeds=(1,)), agent=cassette)
    # length_matched waits for its treatment, which has no cassette, so only three can miss
    assert report.ran == 0 and len(report.missing_cassettes) == 3
    assert isinstance(CassetteMiss("x"), FileNotFoundError)


def test_record_then_replay_reproduces_the_rows(tmp_path) -> None:
    p = plan(seeds=(1, 2))
    rec = CassetteProvider(tmp_path / "c", "record", inner=SimulatedAgent(seed=1),
                           provider_name="sim", model="sim")
    run_experiment(p, rec, provider_name="sim", model="sim", out_dir=tmp_path / "r1",
                   runs_dir=tmp_path / "runs1", source="simulated")
    rep = CassetteProvider(tmp_path / "c", "replay", provider_name="sim", model="sim")
    run_experiment(p, rep, provider_name="sim", model="sim", out_dir=tmp_path / "r2",
                   runs_dir=tmp_path / "runs2", source="simulated")

    def essence(path):
        return [{k: r[k] for k in ("key", "grade", "evidence", "canary_fate", "window_at_probe")}
                for r in read_rows(path)]

    first, second = tmp_path / "r1" / "episodes.jsonl", tmp_path / "r2" / "episodes.jsonl"
    assert essence(first) == essence(second)
    assert rep.misses == 0 and rep.hits > 0


# --- analysis -----------------------------------------------------------------------------------

def test_analysis_reports_rates_intervals_and_paired_comparisons(tmp_path) -> None:
    go(tmp_path, plan(seeds=tuple(range(1, 13))),
       agent=SimulatedAgent(p_follow=1.0, p_keep_in_summary=0.0, seed=2))
    result = analyse(read_rows(tmp_path / "res" / "episodes.jsonl"))
    cells = {c["condition"]: c for c in result["cells"]}
    assert cells["control"]["k_violated"] == 0 and cells["control"]["wilson_lo"] == 0.0
    assert cells["treatment"]["rate"] > cells["length_matched"]["rate"]
    assert cells["treatment"]["verbatim_survival"]["k_kept"] == 0
    comp = {(c["first"], c["second"]): c for c in result["comparisons"]}
    t_vs_c = comp[("treatment(llm_summary)", "control")]
    assert t_vs_c["only_first_failed"] > 0 and t_vs_c["only_second_failed"] == 0
    assert t_vs_c["risk_difference"] > 0 and 0 <= t_vs_c["rd_lo"] <= t_vs_c["rd_hi"] <= 1
    assert 0 < t_vs_c["p_mcnemar"] <= 1 and t_vs_c["q_bh"] >= t_vs_c["p_mcnemar"]
    assert result["source"] == "simulated"


def row(cond: str, seed: int, grade: str, source: str = "simulated") -> dict:
    return {"exp_id": "E", "pack": "constraint", "model_requested": "m", "model_id_reported": "m",
            "condition": cond, "policy": None, "prompt_version": None, "seed": seed, "trial": 0,
            "grade": grade, "date": "2026-10-20", "canary_fate": None, "source": source}


def test_analysis_refuses_to_mix_simulated_and_recorded_rows() -> None:
    with pytest.raises(ValueError, match="refusing to mix"):
        analyse([row("control", 1, "respected"), row("control", 2, "respected", "recorded")])
    with pytest.raises(ValueError, match="no episodes"):
        analyse([])


def test_not_applicable_episodes_are_counted_and_have_a_sensitivity_analysis() -> None:
    rows = [row("control", s, "respected") for s in range(1, 7)]
    rows += [row("treatment", s, "violated") for s in range(1, 5)]
    rows += [row("treatment", 5, "not_applicable"), row("treatment", 6, "not_applicable")]
    out = analyse(rows, primary=[("treatment", "control")])
    cell = next(c for c in out["cells"] if c["condition"] == "treatment")
    assert (cell["n_episodes"], cell["n_graded"], cell["n_not_applicable"]) == (6, 4, 2)
    comp = out["comparisons"][0]
    assert comp["n_pairs"] == 4 and comp["sensitivity_na_as_violated"]["n_pairs"] == 6
    assert comp["sensitivity_na_as_violated"]["only_first_failed"] == 6
    json.dumps(out)  # the result is plain JSON


# --- several policies in one experiment ---------------------------------------------------------

def test_two_policies_share_floor_and_control_but_not_length_matched(tmp_path) -> None:
    for policy in ("recency_truncate", "head_tail"):
        go(tmp_path, plan(policy=policy, seeds=(1, 2, 3)), agent=SimulatedAgent(seed=4))
    rows = read_rows(tmp_path / "res" / "episodes.jsonl")
    by_condition = {c: [r for r in rows if r["condition"] == c] for c in
                    ("floor", "control", "treatment", "length_matched")}
    assert len(by_condition["floor"]) == len(by_condition["control"]) == 3  # run once, reused
    assert len(by_condition["treatment"]) == len(by_condition["length_matched"]) == 6
    sizes = {(r["policy"], r["seed"]): r["window_at_probe"] for r in by_condition["length_matched"]}
    assert len(sizes) == 6  # each policy's twin was sized from its own treatment


def test_analysis_compares_policies_with_each_other_and_with_the_controls(tmp_path) -> None:
    for policy in ("recency_truncate", "head_tail"):
        go(tmp_path, plan(policy=policy, seeds=tuple(range(1, 11))),
           agent=SimulatedAgent(p_follow=1.0, seed=4))
    result = analyse(read_rows(tmp_path / "res" / "episodes.jsonl"),
                     primary=[("treatment(recency_truncate)", "treatment(head_tail)")])
    labels = {c["label"] for c in result["cells"]}
    assert {"treatment(recency_truncate)", "treatment(head_tail)", "control", "floor",
            "length_matched(head_tail)"} <= labels
    (comp,) = result["comparisons"]
    assert comp["first"] == "treatment(recency_truncate)" and comp["risk_difference"] > 0
    assert comp["only_second_failed"] == 0  # head_tail keeps the rule that recency drops
    default = analyse(read_rows(tmp_path / "res" / "episodes.jsonl"))
    assert len(default["comparisons"]) == 4  # two policies x (control, length_matched twin)


def test_different_window_limits_are_separate_cells(tmp_path) -> None:
    for limit in (1800, 3000):
        go(tmp_path, plan(policy="recency_truncate", seeds=(1, 2, 3), limit_tokens=limit),
           agent=SimulatedAgent(p_follow=1.0, seed=4))
    result = analyse(read_rows(tmp_path / "res" / "episodes.jsonl"))
    limits = sorted({c["limit_tokens"] for c in result["cells"]})
    assert limits == [1800, 3000]
    treat = {c["limit_tokens"]: c for c in result["cells"] if c["condition"] == "treatment"}
    assert treat[1800]["rate"] >= treat[3000]["rate"]  # a tighter window loses more


def test_two_models_have_separate_cells_and_neither_skips_the_other(tmp_path) -> None:
    p = plan(seeds=(1, 2))
    for model in ("model-a", "model-b"):
        report = run_experiment(p, SimulatedAgent(seed=1), provider_name="sim", model=model,
                                out_dir=tmp_path / "res", runs_dir=tmp_path / "runs",
                                source="simulated")
        assert (report.ran, report.skipped) == (8, 0)  # the second model is not "already done"
    rows = read_rows(tmp_path / "res" / "episodes.jsonl")
    assert len(rows) == 16 and len({r["key"] for r in rows}) == 16
    assert {r["model_requested"] for r in rows} == {"model-a", "model-b"}
    again = run_experiment(p, SimulatedAgent(seed=1), provider_name="sim", model="model-a",
                           out_dir=tmp_path / "res", runs_dir=tmp_path / "runs",
                           source="simulated")
    assert (again.ran, again.skipped) == (0, 8)  # resume is still per model


def test_two_packs_are_separate_cells_and_never_paired_with_each_other() -> None:
    def in_pack(cond, seed, grade, pack):
        return {**row(cond, seed, grade), "pack": pack}

    rows = [in_pack("control", s, "respected", p) for s in (1, 2, 3)
            for p in ("constraint", "identifier")]
    rows += [in_pack("treatment", s, "violated", "constraint") for s in (1, 2, 3)]
    rows += [in_pack("treatment", s, "respected", "identifier") for s in (1, 2, 3)]
    out = analyse(rows, primary=[("treatment", "control")])
    treat = {c["pack"]: c for c in out["cells"] if c["condition"] == "treatment"}
    assert (treat["constraint"]["n_graded"], treat["constraint"]["k_violated"]) == (3, 3)
    assert (treat["identifier"]["n_graded"], treat["identifier"]["k_violated"]) == (3, 0)
    comps = {c["pack"]: c for c in out["comparisons"]}
    assert comps["constraint"]["n_pairs"] == 3 and comps["constraint"]["only_first_failed"] == 3
    assert comps["identifier"]["only_first_failed"] == 0  # not pooled with the other pack
    assert out["packs"] == ["constraint", "identifier"] and out["pack"] is None
    single = analyse([r for r in rows if r["pack"] == "constraint"])
    assert single["pack"] == "constraint"


def test_exploratory_comparisons_never_enter_the_primary_bh_family() -> None:
    def labelled(cond, policy, seed, grade, model="m"):
        return {**row(cond, seed, grade), "policy": policy, "model_requested": model}

    rows = []
    for model in ("m", "n"):
        rows += [labelled("control", None, s, "respected", model) for s in range(1, 9)]
        broke = range(1, 9) if model == "m" else range(1, 5)  # p = 2/256 for m, 1/8 for n
        rows += [labelled("treatment", "a", s, "violated" if s in broke else "respected", model)
                 for s in range(1, 9)]
        rows += [labelled("length_matched", "a", s, "respected", model) for s in range(1, 9)]
    primary = [("treatment(a)", "control")]
    out = analyse(rows, primary=primary, exploratory="default", bh_family="group")
    roles = [(c["model"], c["second"], c["role"]) for c in out["comparisons"]]
    assert ("m", "control", "primary") in roles
    assert ("m", "length_matched(a)", "exploratory") in roles
    assert ("m", "control", "exploratory") not in roles  # a primary pair is not repeated
    prim = [c for c in out["comparisons"] if c["role"] == "primary"]
    assert all(c["q_bh"] == c["p_mcnemar"] for c in prim)  # a family of one per group
    pooled = analyse(rows, primary=primary, bh_family="all")
    m = next(c for c in pooled["comparisons"] if c["model"] == "m")
    assert m["q_bh"] == pytest.approx(2 * m["p_mcnemar"])  # one family of two: the smaller p rises
    with pytest.raises(ValueError, match="bh_family"):
        analyse(rows, bh_family="per-test")


def test_cells_report_summary_validity_and_whether_behaviour_followed_survival() -> None:
    def treat(seed, fate, grade, valid):
        return {**row("treatment", seed, grade), "canary_fate": fate, "summary_valid": valid}

    rows = [row("control", s, "respected") for s in range(1, 5)]
    rows += [treat(1, "kept", "respected", True), treat(2, "gone", "violated", True),
             treat(3, "gone", "respected", True), treat(4, "gone", "violated", False)]
    cell = next(c for c in analyse(rows)["cells"] if c["condition"] == "treatment")
    assert (cell["n_summary_checked"], cell["n_summary_invalid"]) == (4, 1)
    assert cell["fate_matches_grade"] == {"k": 3, "n": 4}  # seed 3 lost the rule and still obeyed
    control = next(c for c in analyse(rows)["cells"] if c["condition"] == "control")
    assert "n_summary_checked" not in control and "fate_matches_grade" not in control


def test_regrading_from_traces_reproduces_the_rows_and_catches_a_stale_one(tmp_path) -> None:
    from ctxcheck.runner.regrade import regrade_rows

    go(tmp_path, plan(seeds=(1, 2)), agent=SimulatedAgent(p_follow=1.0, seed=4))
    rows = read_rows(tmp_path / "res" / "episodes.jsonl")
    root = Path(".")
    assert regrade_rows(rows, root).changes == []  # a faithful cache changes nothing
    rows[0]["grade"] = "violated" if rows[0]["grade"] == "respected" else "respected"
    stale = regrade_rows(rows, root)
    assert [c[3] for c in stale.changes] == ["grade"]  # only the tampered field is reported
    assert stale.rows[0]["grade"] != rows[0]["grade"]
