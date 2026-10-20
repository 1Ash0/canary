"""observation_mask: keep every message but replace old tool outputs with a short placeholder.

The agent still sees what it did and in what order; it loses what the tools returned. Tool outputs
are usually the bulk of a window, so this often frees enough without dropping anything.

If masking every old output is still not enough, this falls back to dropping the oldest history
(the recency rule), because the window must end under budget (invariant 1). Say so when reporting.
A masked result is a *new* message (new id) and the original is dropped, so the trace records
exactly what was lost.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace

from ctxcheck.harness.types import Message
from ctxcheck.policies.base import PolicyContext
from ctxcheck.policies.units import check_reducible, split, target_for, tokens


class ObservationMask:
    name = "observation_mask"

    def __init__(self, target_ratio: float = 0.6, keep_recent: int = 2) -> None:
        self.target_ratio = target_ratio
        self.keep_recent = keep_recent  # newest tool outputs left unmasked

    def apply(
        self, window: Sequence[Message], budget_tokens: int, ctx: PolicyContext
    ) -> list[Message]:
        if tokens(window) <= budget_tokens:
            return list(window)
        parts = split(window)
        check_reducible(parts, budget_tokens)
        target = target_for(parts, budget_tokens, self.target_ratio)
        units = [list(u) for u in parts.units]
        used = parts.floor + sum(tokens(u) for u in units)

        results = [(ui, mi) for ui, u in enumerate(units) for mi, m in enumerate(u)
                   if m.role == "tool"]
        eligible = results[: max(0, len(results) - self.keep_recent)]
        for ui, mi in eligible:  # oldest first
            if used <= target:
                break
            old = units[ui][mi]
            text = f"[tool output omitted: {old.tokens_est} tokens]"
            n = ctx.count(text)
            if n >= old.tokens_est:
                continue  # masking would not save anything
            units[ui][mi] = replace(old, id=ctx.new_id(), content=text, tokens_est=n)
            used -= old.tokens_est - n

        while units and used > target:  # fallback: drop the oldest units
            used -= tokens(units.pop(0))
        return parts.flatten(units)
