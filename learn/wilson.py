"""
learn/wilson.py — U5 Wilson score interval

Run:  uv run python learn/wilson.py

What this shows:
  1. wilson_interval(k, n) — the right confidence interval for a proportion
  2. Why the normal approximation breaks at extremes (k=0, k=n, small n)
  3. The ±18pp intuition: at n=30, you cannot distinguish 40% from 55%
  4. Why pairing (same seeds, two conditions) buys statistical power cheaply
  5. Sanity check: at k=0, n=10 the interval does NOT include 0.5

The real stats module lives in src/ctxcheck/stats/ (built in M4).
"""

from __future__ import annotations

import math


# ── Wilson score interval ────────────────────────────────────────────────────
# Formula (Agresti & Coull 1998):
#
#   p̂  = k / n
#   centre = (p̂ + z²/2n) / (1 + z²/n)
#   margin = z * sqrt( p̂(1-p̂)/n + z²/4n² ) / (1 + z²/n)
#   lower, upper = centre ∓ margin
#
# The z²/n terms are what make Wilson correct near 0 and 1:
# they "pull" the interval toward 0.5, preventing it from going
# below 0 or above 1 even when k=0 or k=n.

def wilson_interval(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """
    95% Wilson score interval for k successes in n trials.

    Args:
        k: number of violations (successes)
        n: total trials
        z: z-score for desired confidence (1.96 = 95%, 2.576 = 99%)

    Returns:
        (lower, upper) as fractions in [0, 1]
    """
    if n == 0:
        raise ValueError("n must be > 0")
    if not (0 <= k <= n):
        raise ValueError(f"k must be between 0 and n, got k={k}, n={n}")

    p_hat = k / n
    z2 = z * z
    denom = 1 + z2 / n

    centre = (p_hat + z2 / (2 * n)) / denom
    margin = (z / denom) * math.sqrt(p_hat * (1 - p_hat) / n + z2 / (4 * n * n))

    return (max(0.0, centre - margin), min(1.0, centre + margin))


def normal_interval(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Normal approximation — for comparison only. Breaks at extremes."""
    p = k / n
    margin = z * math.sqrt(p * (1 - p) / n)
    return (p - margin, p + margin)


# ── helpers ──────────────────────────────────────────────────────────────────

def fmt(interval: tuple[float, float]) -> str:
    lo, hi = interval
    return f"[{lo:.3f}, {hi:.3f}]  (width={hi - lo:.3f})"

def width(interval: tuple[float, float]) -> float:
    return interval[1] - interval[0]


# ── demo ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":

    # ── 1. Basic interval at a mid-range rate ────────────────────────────────
    print("── 1. basic: k=12, n=30 (rate=40%) ───────────────────────────")
    k, n = 12, 30
    w = wilson_interval(k, n)
    nr = normal_interval(k, n)
    print(f"  Wilson  : {fmt(w)}")
    print(f"  Normal  : {fmt(nr)}")
    print(f"  Wilson pulls the interval slightly; normal is close here (rate not extreme)")

    # ── 2. Why normal breaks at k=0 ──────────────────────────────────────────
    print("\n── 2. extreme: k=0, n=10 (rate=0%) ───────────────────────────")
    w0 = wilson_interval(0, 10)
    nr0 = normal_interval(0, 10)
    print(f"  Wilson  : {fmt(w0)}")
    print(f"  Normal  : {fmt(nr0)}")
    print(f"  Normal gives [{nr0[0]:.3f}, {nr0[1]:.3f}] — lower is exactly 0.000, upper is 0.000")
    print(f"  That says 'we're 95% sure the rate is exactly 0' — nonsense with n=10")
    print(f"  Wilson says the rate could be as high as {w0[1]:.3f} — honest for small n")

    # ── 3. Sanity check: k=0, n=10 interval must NOT include 0.5 ────────────
    print("\n── 3. sanity check ────────────────────────────────────────────")
    lo, hi = wilson_interval(0, 10)
    includes_half = lo <= 0.5 <= hi
    print(f"  wilson_interval(0, 10) = [{lo:.4f}, {hi:.4f}]")
    print(f"  includes 0.5?  {includes_half}  (must be False)")
    assert not includes_half, "sanity check failed"
    print(f"  ✓ passed — even with 0 violations, we can rule out a 50% rate")

    # ── 4. The ±18pp claim: n=30 near 50% ───────────────────────────────────
    print("\n── 4. n=30 power: can we tell 40% from 55%? ───────────────────")
    w40 = wilson_interval(12, 30)   # 40% rate
    w55 = wilson_interval(17, 30)   # ~57% rate (closest integer to 55%)
    print(f"  k=12/30 (40%): {fmt(w40)}")
    print(f"  k=17/30 (57%): {fmt(w55)}")
    overlap = w40[1] > w55[0]
    print(f"  intervals overlap? {overlap}")
    print(f"  → at n=30 these two rates are NOT distinguishable")
    print(f"  → you need more trials OR a paired design to tell them apart")

    # ── 5. Paired design intuition ───────────────────────────────────────────
    print("\n── 5. paired design: why same seeds helps ─────────────────────")
    print("""
  Unpaired (two independent groups of 30):
    control:   30 different seeds → 30 outcomes
    treatment: 30 different seeds → 30 outcomes
    You're comparing two noisy samples; shared background variance inflates
    the uncertainty.

  Paired (same 30 seeds under both conditions):
    seed 01:  control=respected, treatment=violated  ← discordant (counts)
    seed 02:  control=respected, treatment=respected ← concordant (cancels)
    seed 03:  control=violated,  treatment=violated  ← concordant (cancels)
    ...
    McNemar only counts the DISCORDANT pairs. Trials where both conditions
    agree tell you nothing about the *difference* — they cancel. The signal
    comes purely from the trials where conditions disagree.
    With 30 seeds you get up to 30 discordant pairs instead of pooling 60
    noisy independent draws. Same n, more signal.
    """)

    # ── 6. Quick table: how interval shrinks with n ──────────────────────────
    print("── 6. interval width vs n (rate=50%, k=n/2) ───────────────────")
    print(f"  {'n':>6}  {'k':>6}  {'width':>8}  interval")
    for n_val in [10, 20, 30, 50, 100, 200]:
        k_val = n_val // 2
        iv = wilson_interval(k_val, n_val)
        print(f"  {n_val:>6}  {k_val:>6}  {width(iv):>8.3f}  {fmt(iv)}")
    print()
    print("  Rule of thumb: halving the interval width requires 4× the trials.")
