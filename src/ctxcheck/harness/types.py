"""Plain data types shared by the loop, tools and providers.

One model reply holds at most one tool call (the design rule "one terminal action", EVAL_DESIGN §2),
so grading a run means parsing one call's arguments, not interpreting prose.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Role = Literal["system", "user", "assistant", "tool"]
Origin = Literal["user", "assistant", "tool", "summary", "canary"]


@dataclass(frozen=True)
class Message:
    id: str
    role: Role
    content: str
    origin: Origin
    tokens_est: int
    step: int  # which user turn this message belongs to
    call_id: str | None = None  # set on the assistant message that makes a call and on its result


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    args: dict[str, Any]


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    input_schema: dict[str, Any]


@dataclass(frozen=True)
class ModelResponse:
    text: str = ""
    tool_call: ToolCall | None = None  # None means the model is done with this turn (end_turn)
    input_tokens: int = 0
    output_tokens: int = 0
    model_id: str = "scripted"
    extra: dict[str, Any] = field(default_factory=dict)
