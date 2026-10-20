"""Policy registry. A new policy is one file implementing `Policy`, plus an entry here."""

from __future__ import annotations

from typing import Any

from ctxcheck.policies.base import (
    IrreducibleBudget,
    Policy,
    PolicyContext,
    PolicyError,
    SummaryFailed,
)
from ctxcheck.policies.head_tail import HeadTail
from ctxcheck.policies.mask import ObservationMask
from ctxcheck.policies.recency import RecencyTruncate
from ctxcheck.policies.summarize import PROMPTS, LLMSummary

REGISTRY: dict[str, type] = {
    "recency_truncate": RecencyTruncate,
    "head_tail": HeadTail,
    "observation_mask": ObservationMask,
    "llm_summary": LLMSummary,
}
DETERMINISTIC = ("recency_truncate", "head_tail", "observation_mask")


def make_policy(name: str, **options: Any) -> Policy:
    if name not in REGISTRY:
        raise ValueError(f"unknown policy {name!r}; known: {', '.join(sorted(REGISTRY))}")
    return REGISTRY[name](**options)


__all__ = [
    "DETERMINISTIC", "PROMPTS", "REGISTRY", "HeadTail", "IrreducibleBudget", "LLMSummary",
    "ObservationMask", "Policy", "PolicyContext", "PolicyError", "RecencyTruncate",
    "SummaryFailed", "make_policy",
]
