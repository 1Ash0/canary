"""recency_truncate: drop the oldest history until the window is under the target.

The simplest policy and the baseline the others are compared with. It keeps the newest, so a fact
stated early is the first to go.
"""

from __future__ import annotations

from collections.abc import Sequence

from ctxcheck.harness.types import Message
from ctxcheck.policies.base import PolicyContext
from ctxcheck.policies.units import check_reducible, split, target_for, tokens


class RecencyTruncate:
    name = "recency_truncate"

    def __init__(self, target_ratio: float = 0.6) -> None:
        self.target_ratio = target_ratio

    def apply(
        self, window: Sequence[Message], budget_tokens: int, ctx: PolicyContext
    ) -> list[Message]:
        if tokens(window) <= budget_tokens:
            return list(window)  # idempotent: nothing to do when already under budget
        parts = split(window)
        check_reducible(parts, budget_tokens)
        target = target_for(parts, budget_tokens, self.target_ratio)
        units = list(parts.units)
        used = parts.floor + sum(tokens(u) for u in units)
        while units and used > target:
            used -= tokens(units.pop(0))
        return parts.flatten(units)
