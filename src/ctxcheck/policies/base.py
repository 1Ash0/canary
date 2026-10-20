"""The Policy seam: decides what stays in the window when it is over budget.

The loop owns message ids and token counting, so a policy that adds a message (a summary, a masked
tool result) builds it through the context it is handed. Deterministic policies are pure functions
of (window, budget). The LLM policy gets the loop's own provider through the context, so its calls
go through the same budget guard and cassettes as the agent's, and are logged as model calls.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol

from ctxcheck.harness.types import Message, ModelResponse
from ctxcheck.providers.base import Provider


class PolicyError(Exception):
    """A policy could not produce a window. The loop ends the run with `code` as the reason."""

    code = "policy_error"


class IrreducibleBudget(PolicyError):
    """The protected messages (system prompt and the current turn) alone exceed the budget.

    Raised instead of silently overrunning (invariant 1): no policy can fix this by dropping.
    """

    code = "irreducible_budget"


class SummaryFailed(PolicyError):
    code = "summary_failed"


@dataclass(frozen=True)
class PolicyContext:
    step: int  # the user turn being compacted before
    new_id: Callable[[], str]  # fresh message id, unique within the run
    count: Callable[[str], int]  # token estimate for a string
    trial_index: int = 0
    provider: Provider | None = None  # for policies that call a model
    params: dict[str, Any] = field(default_factory=dict)
    # logs a model call the policy made, so it appears in the trace like any other
    record_call: Callable[[ModelResponse, Sequence[Message]], None] | None = None


class Policy(Protocol):
    name: str

    def apply(
        self, window: Sequence[Message], budget_tokens: int, ctx: PolicyContext
    ) -> list[Message]:
        """Return the new window. Messages kept must be the same objects; new ones are additions."""
        ...
