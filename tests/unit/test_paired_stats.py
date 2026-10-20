"""Exact McNemar, paired bootstrap and Benjamini-Hochberg, against hand-computed values."""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from ctxcheck.stats import benjamini_hochberg, mcnemar_exact, paired_bootstrap_rd


def test_mcnemar_five_to_zero_is_two_over_thirty_two_doubled() -> None:
    # P(X<=0) with n=5 is 1/32; two-sided is 2/32 = 0.0625
    assert mcnemar_exact(5, 0) == pytest.approx(0.0625)
    assert mcnemar_exact(0, 5) == pytest.approx(0.0625)


def test_mcnemar_ten_to_zero() -> None:
    assert mcnemar_exact(10, 0) == pytest.approx(2 / 1024)


def test_mcnemar_balanced_disagreement_is_not_significant() -> None:
    assert mcnemar_exact(4, 4) == 1.0
    assert mcnemar_exact(3, 4) == 1.0


def test_mcnemar_no_discordant_pairs_has_nothing_to_say() -> None:
    assert mcnemar_exact(0, 0) == 1.0


def test_mcnemar_seven_to_two() -> None:
    # n=9, P(X<=2) = (1+9+36)/512 = 46/512, doubled = 92/512
    assert mcnemar_exact(7, 2) == pytest.approx(92 / 512)


def test_mcnemar_rejects_negative_counts() -> None:
    with pytest.raises(ValueError):
        mcnemar_exact(-1, 2)


@given(st.integers(0, 40), st.integers(0, 40))
def test_mcnemar_is_symmetric_and_a_probability(b: int, c: int) -> None:
    p = mcnemar_exact(b, c)
    assert p == mcnemar_exact(c, b) and 0.0 < p <= 1.0


def test_bootstrap_difference_and_interval_contain_the_point_estimate() -> None:
    pairs = [(True, False)] * 6 + [(False, False)] * 4  # first fails 6/10, second 0/10
    rd, lo, hi = paired_bootstrap_rd(pairs, resamples=2000, seed=1)
    assert rd == pytest.approx(0.6) and lo <= rd <= hi and 0.2 < lo and hi <= 1.0


def test_bootstrap_with_no_difference_straddles_zero() -> None:
    pairs = [(True, True)] * 3 + [(False, False)] * 7
    rd, lo, hi = paired_bootstrap_rd(pairs, resamples=2000, seed=1)
    assert rd == 0.0 and lo == 0.0 and hi == 0.0  # every resample has identical pairs


def test_bootstrap_is_reproducible_with_a_seed() -> None:
    pairs = [(True, False)] * 4 + [(False, True)] * 2 + [(False, False)] * 6
    assert paired_bootstrap_rd(pairs, 1000, seed=5) == paired_bootstrap_rd(pairs, 1000, seed=5)


def test_bootstrap_needs_two_pairs() -> None:
    with pytest.raises(ValueError):
        paired_bootstrap_rd([(True, False)])


def test_bh_matches_the_textbook_example() -> None:
    # sorted .005 .01 .03 .04, m=4 -> .02 .02 .04 .04 (monotone step-up)
    q = benjamini_hochberg([0.01, 0.04, 0.03, 0.005])
    assert q == pytest.approx([0.02, 0.04, 0.04, 0.02])


def test_bh_never_reduces_a_p_value_and_stays_a_probability() -> None:
    ps = [0.001, 0.2, 0.5, 0.03, 0.9]
    q = benjamini_hochberg(ps)
    assert all(qi >= pi for qi, pi in zip(q, ps, strict=True)) and max(q) <= 1.0


def test_bh_single_p_value_is_unchanged() -> None:
    assert benjamini_hochberg([0.03]) == [0.03]


@given(st.lists(st.floats(0.0, 1.0), min_size=1, max_size=20))
def test_bh_preserves_order_of_significance(ps: list[float]) -> None:
    q = benjamini_hochberg(ps)
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    assert all(q[order[i]] <= q[order[i + 1]] + 1e-12 for i in range(len(ps) - 1))
