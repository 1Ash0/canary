"""Wilson score interval for a proportion (ported from learn/wilson.py, gate G5).

    p̂ = k / n
    centre = (p̂ + z²/2n) / (1 + z²/n)
    margin = z * sqrt(p̂(1-p̂)/n + z²/4n²) / (1 + z²/n)

The z²/n terms keep the interval inside [0, 1] and honest at k=0 or k=n, where the normal
approximation collapses to a zero-width interval.
"""

from __future__ import annotations

import math


def wilson_interval(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% Wilson interval for k successes in n trials, as fractions in [0, 1]."""
    if n <= 0:
        raise ValueError("n must be > 0")
    if not 0 <= k <= n:
        raise ValueError(f"k must be between 0 and n, got k={k}, n={n}")

    p_hat = k / n
    z2 = z * z
    denom = 1 + z2 / n
    centre = (p_hat + z2 / (2 * n)) / denom
    margin = (z / denom) * math.sqrt(p_hat * (1 - p_hat) / n + z2 / (4 * n * n))
    # k=0 -> lower is exactly 0 and k=n -> upper is exactly 1; floating point leaves ~1e-17 behind
    lower = 0.0 if k == 0 else max(0.0, centre - margin)
    upper = 1.0 if k == n else min(1.0, centre + margin)
    return (lower, upper)
