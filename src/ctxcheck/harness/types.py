"""Plain data types shared by the loop, tools and providers.

One model reply holds at most one tool call (the design rule "one terminal action", EVAL_DESIGN §2),
so grading a run means parsing one call's arguments, not interpreting prose.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

# An adapter that cannot decode a model's tool arguments passes the raw text under this key, so the
# dispatcher can tell the model the real problem instead of a misleading "missing argument".
BAD_ARGS_KEY = "_unparsed_arguments"

Role = Literal["system", "user", "assistant", "tool"]
Origin = Literal["user", "assistant", "tool", "summary", "canary"]


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    args: dict[str, Any]


@dataclass(frozen=True)
class Message:
    id: str
    role: Role
    content: str
    origin: Origin
    tokens_est: int
    step: int  # which user turn this message belongs to
    call_id: str | None = None  # set on the assistant message that makes a call and on its result
    # Structured detail an adapter needs to rebuild a provider request. `content` stays the readable
    # text the trace records and the tokenizer counts.
    tool_call: ToolCall | None = None  # on the assistant message that made a call
    lead_in: str = ""  # the text the model wrote before the call
    is_error: bool = False  # on a tool message whose call failed


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
    cache_read_input_tokens: int | None = None  # recorded when the provider reports it
    cache_creation_input_tokens: int | None = None
    model_id: str = "scripted"
    extra: dict[str, Any] = field(default_factory=dict)
