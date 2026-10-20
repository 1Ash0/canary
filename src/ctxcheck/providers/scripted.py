"""A provider that returns pre-written replies in order. No network, no cost, fully deterministic.

It is what lets the loop be built and tested offline. It records every request it received so a test
can check exactly what the loop sent (messages, tools, trial_index).
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from ctxcheck.harness.types import Message, ModelResponse, ToolSpec


class ScriptExhausted(Exception):
    """The loop asked for more replies than the script holds."""


class ScriptedProvider:
    def __init__(self, replies: Sequence[ModelResponse]) -> None:
        self._replies = list(replies)
        self.requests: list[dict[str, Any]] = []

    def complete(
        self,
        messages: Sequence[Message],
        tools: Sequence[ToolSpec],
        params: dict[str, Any],
        trial_index: int,
    ) -> ModelResponse:
        request = {"messages": list(messages), "tools": list(tools)}
        self.requests.append({**request, "params": params, "trial": trial_index})
        if len(self.requests) > len(self._replies):
            raise ScriptExhausted(
                f"script has {len(self._replies)} replies, call {len(self.requests)}"
            )
        return self._replies[len(self.requests) - 1]
