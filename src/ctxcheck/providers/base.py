"""The Provider seam: anything that can answer one model call. Adding a provider is one file."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol

from ctxcheck.harness.types import Message, ModelResponse, ToolSpec


class Provider(Protocol):
    def complete(
        self,
        messages: Sequence[Message],
        tools: Sequence[ToolSpec],
        params: dict[str, Any],
        trial_index: int,
    ) -> ModelResponse: ...
