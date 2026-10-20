"""head_tail: keep the start of the history and the end, drop the middle.

The start of a session is where instructions usually live, so this tests the hypothesis that early
facts survive when the head is protected. `head_ratio` is the share of the space left over (after
the system prompt and current turn) given to the head; the rest goes to the newest history.
"""

from __future__ import annotations

from collections.abc import Sequence

from ctxcheck.harness.types import Message
from ctxcheck.policies.base import PolicyContext
from ctxcheck.policies.units import check_reducible, split, target_for, tokens


class HeadTail:
    name = "head_tail"

    def __init__(self, target_ratio: float = 0.6, head_ratio: float = 0.3) -> None:
        self.target_ratio = target_ratio
        self.head_ratio = head_ratio

    def apply(
        self, window: Sequence[Message], budget_tokens: int, ctx: PolicyContext
    ) -> list[Message]:
        if tokens(window) <= budget_tokens:
            return list(window)
        parts = split(window)
        check_reducible(parts, budget_tokens)
        room = target_for(parts, budget_tokens, self.target_ratio) - parts.floor
        head_room = int(room * self.head_ratio)

        head: list[list[Message]] = []
        used = 0
        for unit in parts.units:
            if used + tokens(unit) > head_room:
                break  # a contiguous prefix, never a gap
            head.append(unit)
            used += tokens(unit)

        tail: list[list[Message]] = []
        for unit in reversed(parts.units[len(head):]):
            if used + tokens(unit) > room:
                break
            tail.append(unit)
            used += tokens(unit)
        tail.reverse()
        return parts.flatten([*head, *tail])
