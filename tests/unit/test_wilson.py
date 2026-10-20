"""Wilson interval: known values, the two edge cases, and properties that must always hold."""

import math

import pytest
from hypothesis import given
from hypothesis import strategies as st

from ctxcheck.stats import wilson_interval


def test_known_value_12_of_30() -> None:
    # by hand: z^2=3.8416, denom=1.12805, centre=0.41137, margin=0.16545
    lo, hi = wilson_interval(12, 30)
    assert lo == pytest.approx(0.2459, abs=1e-3)
    assert hi == pytest.approx(0.5768, abs=1e-3)


def test_zero_of_ten_rules_out_a_fifty_percent_rate() -> None:
    lo, hi = wilson_interval(0, 10)
    assert lo == 0.0
    assert hi < 0.5  # sanity check from the G5 demo


def test_all_of_ten_is_honest_at_the_top_too() -> None:
    lo, hi = wilson_interval(10, 10)
    assert hi == 1.0
    assert lo > 0.5


def test_zero_successes_has_a_nonzero_upper_bound() -> None:
    # the normal approximation would give [0, 0] here
    assert wilson_interval(0, 10)[1] > 0.2


def test_forty_and_fifty_seven_percent_overlap_at_n_30() -> None:
    assert wilson_interval(12, 30)[1] > wilson_interval(17, 30)[0]


def test_width_shrinks_roughly_with_sqrt_n() -> None:
    def width(n: int) -> float:
        lo, hi = wilson_interval(n // 2, n)
        return hi - lo

    assert width(100) < width(50) < width(30) < width(10)
    assert width(100) / width(400) == pytest.approx(2, rel=0.1)  # 4x the trials, half the width


@pytest.mark.parametrize(("k", "n"), [(0, 0), (1, 0), (-1, 5), (6, 5)])
def test_invalid_inputs_are_rejected(k: int, n: int) -> None:
    with pytest.raises(ValueError):
        wilson_interval(k, n)


_k_and_n = st.integers(min_value=1, max_value=500).flatmap(
    lambda n: st.tuples(st.integers(0, n), st.just(n))
)


@given(_k_and_n)
def test_interval_is_ordered_inside_unit_range_and_contains_the_rate(kn: tuple[int, int]) -> None:
    k, n = kn
    lo, hi = wilson_interval(k, n)
    assert 0.0 <= lo <= hi <= 1.0
    assert lo <= k / n <= hi + 1e-12
    assert not math.isnan(lo + hi)
