"""Paired comparisons: exact McNemar, bootstrap risk difference, Benjamini-Hochberg.

Pairing is the main way to buy power cheaply (EVAL_DESIGN §5): the same seed is run under two
conditions, and only the pairs that *disagree* carry information about the difference.
"""

from __future__ import annotations

import math
import random
from collections.abc import Sequence


def mcnemar_exact(b: int, c: int) -> float:
    """Two-sided exact p-value for discordant counts b and c (null: each is equally likely).

    b = pairs where only the first condition failed, c = only the second. Under the null the
    discordant pairs split like fair coin flips, so the p-value is a binomial tail.
    """
    if b < 0 or c < 0:
        raise ValueError("counts cannot be negative")
    n = b + c
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, i) for i in range(min(b, c) + 1)) / 2**n
    return min(1.0, 2 * tail)


def paired_bootstrap_rd(
    pairs: Sequence[tuple[bool, bool]], resamples: int = 10_000, seed: int = 0, level: float = 0.95
) -> tuple[float, float, float]:
    """Risk difference (first minus second), with a percentile bootstrap interval over pairs.

    Each pair is (first failed, second failed). Resampling whole pairs keeps the pairing intact.
    Returns (difference, low, high). The interval is not defined for fewer than two pairs.
    """
    n = len(pairs)
    if n < 2:
        raise ValueError("need at least two pairs for an interval")
    rd = sum(a for a, _ in pairs) / n - sum(b for _, b in pairs) / n
    rnd = random.Random(seed)
    diffs = sorted(
        sum(pairs[i][0] - pairs[i][1] for i in (rnd.randrange(n) for _ in range(n))) / n
        for _ in range(resamples)
    )
    alpha = (1 - level) / 2
    lo, hi = int(alpha * resamples), min(resamples - 1, int((1 - alpha) * resamples))
    return rd, diffs[lo], diffs[hi]


def benjamini_hochberg(pvalues: Sequence[float]) -> list[float]:
    """Adjusted p-values (q-values) controlling the false discovery rate, in input order."""
    m = len(pvalues)
    order = sorted(range(m), key=lambda i: pvalues[i])
    adjusted = [0.0] * m
    running = 1.0
    for rank in range(m, 0, -1):  # from the largest p down, keep the running minimum
        i = order[rank - 1]
        running = min(running, pvalues[i] * m / rank)
        adjusted[i] = running
    return adjusted
