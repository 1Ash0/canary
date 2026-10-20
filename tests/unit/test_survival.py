"""The mechanical survival grid: real policy code, seeded histories, no model."""

from ctxcheck.runner.survival import survival_grid


def grid(**kw):
    kw.setdefault("seeds", 3)
    kw.setdefault("positions", (0, 6, 12, 17))
    kw.setdefault("budgets", (1200, 2400, 3600))
    return survival_grid(**kw)


def rate(g, policy, position, budget):
    return next(c["rate"] for c in g["cells"] if (c["policy"], c["position"], c["budget"])
                == (policy, position, budget))


def test_the_grid_is_labelled_deterministic_and_says_no_model_was_called() -> None:
    g = grid(policies=("recency_truncate",))
    assert g["epistemic"] == "deterministic" and "No model" in g["description"]
    assert len(g["cells"]) == 1 * 4 * 3


def test_recency_survival_never_decreases_for_later_positions_or_larger_budgets() -> None:
    g = grid(policies=("recency_truncate",))
    for budget in g["budgets"]:
        rates = [rate(g, "recency_truncate", p, budget) for p in g["positions"]]
        assert rates == sorted(rates)
    for position in g["positions"]:
        rates = [rate(g, "recency_truncate", position, b) for b in g["budgets"]]
        assert rates == sorted(rates)


def test_recency_loses_the_earliest_fact_and_keeps_the_latest() -> None:
    g = grid(policies=("recency_truncate",))
    assert rate(g, "recency_truncate", 0, 1200) == 0.0
    assert rate(g, "recency_truncate", 17, 1200) == 1.0


def test_head_tail_protects_the_very_start_that_recency_loses() -> None:
    g = grid(policies=("recency_truncate", "head_tail"))
    assert rate(g, "head_tail", 0, 1200) == 1.0 and rate(g, "recency_truncate", 0, 1200) == 0.0


def test_the_grid_is_reproducible() -> None:
    assert grid(policies=("head_tail",)) == grid(policies=("head_tail",))


def test_cells_carry_wilson_intervals_and_counts() -> None:
    g = grid(policies=("observation_mask",))
    for c in g["cells"]:
        assert 0 <= c["k_kept"] <= c["n"] and c["n"] > 0
        assert c["wilson_lo"] <= c["rate"] <= c["wilson_hi"]
