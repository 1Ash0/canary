"""Shared pieces for the deterministic policies: what may be dropped, and in what pieces.

Three parts of a window: the system prompt (never dropped), the current turn (the last real user
message and everything after it: never dropped, because the agent is mid-task), and the history in
between. History is cut into *units*: a tool call and its result are one unit, so a policy can never
keep one without the other (invariant 2; providers reject orphans).
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from ctxcheck.harness.types import Message
from ctxcheck.policies.base import IrreducibleBudget


def tokens(messages: Iterable[Message]) -> int:
    return sum(m.tokens_est for m in messages)


@dataclass(frozen=True)
class Split:
    system: list[Message]
    units: list[list[Message]]  # history, oldest first
    tail: list[Message]  # the current turn

    @property
    def floor(self) -> int:
        """The least a policy can leave: system plus the current turn."""
        return tokens(self.system) + tokens(self.tail)

    def flatten(self, units: Sequence[list[Message]]) -> list[Message]:
        return [*self.system, *(m for u in units for m in u), *self.tail]


def split(window: Sequence[Message]) -> Split:
    n_sys = 0
    while n_sys < len(window) and window[n_sys].role == "system":
        n_sys += 1
    rest = list(window[n_sys:])
    # a summary is a user-role message but not a user turn: it is history, and may be re-summarised
    turn_starts = [i for i, m in enumerate(rest) if m.role == "user" and m.origin != "summary"]
    tail_at = turn_starts[-1] if turn_starts else len(rest)
    history, tail = rest[:tail_at], rest[tail_at:]

    units: list[list[Message]] = []
    i = 0
    while i < len(history):
        m = history[i]
        nxt = history[i + 1] if i + 1 < len(history) else None
        if m.tool_call is not None and nxt is not None and nxt.role == "tool" \
                and nxt.call_id == m.call_id:
            units.append([m, nxt])
            i += 2
        else:
            units.append([m])
            i += 1
    return Split(list(window[:n_sys]), units, tail)


def check_reducible(parts: Split, budget_tokens: int) -> None:
    if parts.floor > budget_tokens:
        raise IrreducibleBudget(
            f"the system prompt and current turn need {parts.floor} tokens but the budget "
            f"is {budget_tokens}; no policy can drop them"
        )


def target_for(parts: Split, budget_tokens: int, ratio: float) -> int:
    """Compact below the limit, not to it, so the very next message does not trigger again."""
    return max(parts.floor, int(budget_tokens * ratio))
