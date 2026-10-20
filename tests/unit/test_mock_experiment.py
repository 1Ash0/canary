"""The mock experiment must be deterministic, internally consistent and unmistakably labelled."""

from ctxcheck.mock_experiment import ASSUMED_RATES, run_mock
from ctxcheck.stats import wilson_interval


def test_same_seed_same_result_different_seed_different_result() -> None:
    assert run_mock(1) == run_mock(1)
    assert run_mock(1) != run_mock(2)


def test_is_labelled_simulated_and_states_its_assumptions() -> None:
    result = run_mock()
    assert result["epistemic"] == "simulated" and result["label"] == "mock data"
    assert result["assumed_rates"] == ASSUMED_RATES
    assert "No model was called" in result["note"]


def test_counts_agree_with_the_trials() -> None:
    result = run_mock(1, n=10)
    for condition, cell in result["cells"].items():
        k = sum(t[condition] == "violated" for t in result["trials"])
        assert (cell["k"], cell["n"]) == (k, 10)
        assert cell["rate"] == k / 10


def test_intervals_come_from_wilson_and_contain_the_rate() -> None:
    for cell in run_mock()["cells"].values():
        assert (cell["wilson_lo"], cell["wilson_hi"]) == wilson_interval(cell["k"], cell["n"])
        assert cell["wilson_lo"] <= cell["rate"] <= cell["wilson_hi"]


def test_paired_counts_add_up_to_n_and_match_the_cells() -> None:
    result = run_mock(1, n=10)
    p, cells = result["paired"], result["cells"]
    assert sum(p.values()) == 10
    assert p["both_violated"] + p["only_control_violated"] == cells["control"]["k"]
    assert p["both_violated"] + p["only_treatment_violated"] == cells["recency_truncate"]["k"]


def test_every_trial_has_a_seed_and_a_valid_outcome_per_condition() -> None:
    trials = run_mock(3, n=10)["trials"]
    assert [t["seed"] for t in trials] == list(range(1, 11))
    assert all(t[c] in ("violated", "respected") for t in trials for c in ASSUMED_RATES)
