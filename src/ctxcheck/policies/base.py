"""The Policy seam: decides what stays in the window when it is over budget.

The loop owns message ids and token counting, so a policy that adds a message (a summary) builds it
through the context it is handed. Deterministic policies are pure functions of (window, budget).
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Protocol

from ctxcheck.harness.types import Message


@dataclass(frozen=True)
class PolicyContext:
    step: int  # the user turn being compacted before
    new_id: Callable[[], str]  # fresh message id, unique within the run
    count: Callable[[str], int]  # token estimate for a string


class Policy(Protocol):
    name: str

    def apply(
        self, window: Sequence[Message], budget_tokens: int, ctx: PolicyContext
    ) -> list[Message]:
        """Return the new window. Messages kept must be the same objects; new ones are additions."""
        ...
