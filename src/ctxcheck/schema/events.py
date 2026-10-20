"""Trace event schema, pydantic v2, single source of truth.

The JSONL trace is the source of truth for every run (docs/ARCHITECTURE.md). Every view the web app
shows is derived by replaying these events, including canary fate (kept / changed / gone), which is
computed from `canary_planted` + `compaction` + the summary text and is deliberately not an event.
Bump schema_version when fields change: additive = minor, breaking = major plus a migration.
0.2: added optional run_end.reason (additive; 0.1 traces still parse).
0.3: added optional compaction.prompt_version (the llm_summary prompt version) and the grade
`not_applicable` on canary_probe (no accepted call to the watched tool). Both additive.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

Role = Literal["system", "user", "assistant", "tool"]
Origin = Literal["user", "assistant", "tool", "summary", "canary"]


class _Base(BaseModel):
    # forbid: a misspelled field is an error, not silently dropped
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "0.3"
    run_id: str
    seq: int = Field(ge=0)  # monotonic logical clock; orders events even when timestamps tie
    ts: str  # ISO-8601


class RunStartEvent(_Base):
    type: Literal["run_start"]
    scenario_id: str
    seed: int
    policy: str
    provider: str
    model: str
    params: dict[str, Any] = Field(default_factory=dict)
    harness_git_sha: str = "unknown"
    limit_tokens: int = Field(gt=0)  # window budget the harness compacts against
    tools_tokens_est: int = Field(ge=0)  # tool specs are fixed for the run


class MessageEvent(_Base):
    type: Literal["message"]
    message_id: str
    step: int = Field(ge=1)  # turn number
    role: Role
    content: str
    tokens_est: int = Field(ge=0)  # local tokenizer estimate
    origin: Origin


class ModelCallEvent(_Base):
    type: Literal["model_call"]
    request_hash: str
    trial_index: int = Field(ge=0)
    model_id_reported: str
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    cache_read_input_tokens: int | None = None  # recorded when the API reports it, never simulated
    cache_creation_input_tokens: int | None = None
    cassette_hit: bool
    cost_usd: float = Field(ge=0)


class ToolCallEvent(_Base):
    type: Literal["tool_call"]
    call_id: str
    name: str
    args: dict[str, Any]


class ToolResultEvent(_Base):
    type: Literal["tool_result"]
    call_id: str
    result: str
    is_error: bool = False


class CompactionEvent(_Base):
    type: Literal["compaction"]
    policy: str
    trigger: str
    tokens_before: int = Field(ge=0)
    tokens_after: int = Field(ge=0)
    kept_ids: list[str]
    dropped_ids: list[str]
    added_ids: list[str]
    cost_usd: float = Field(default=0.0, ge=0)
    summary_message_id: str | None = None
    prompt_version: str | None = None  # added in 0.3: set by policies that call a model


class CanaryPlantedEvent(_Base):
    type: Literal["canary_planted"]
    canary_id: str
    canary_type: str
    message_id: str
    value: str  # the planted fact, verbatim


class CanaryProbeEvent(_Base):
    type: Literal["canary_probe"]
    canary_id: str
    probe_message_id: str
    grade: Literal["violated", "respected", "not_applicable"]  # n/a added in 0.3
    evidence: str


class RunEndEvent(_Base):
    type: Literal["run_end"]
    status: Literal["ok", "error", "aborted"]
    reason: str | None = None  # added in 0.2: why the run stopped (end_turn, terminal_tool, ...)
    totals: dict[str, float] = Field(default_factory=dict)


# One entry per event type. The `type` field tells pydantic which class to validate against.
TraceEvent = Annotated[
    RunStartEvent
    | MessageEvent
    | ModelCallEvent
    | ToolCallEvent
    | ToolResultEvent
    | CompactionEvent
    | CanaryPlantedEvent
    | CanaryProbeEvent
    | RunEndEvent,
    Field(discriminator="type"),
]

_adapter: TypeAdapter[TraceEvent] = TypeAdapter(TraceEvent)


def parse_event(line: str) -> TraceEvent:
    """Parse one JSONL line into its event class. Raises pydantic.ValidationError if invalid."""
    return _adapter.validate_json(line)


def event_json_schema() -> dict[str, Any]:
    """JSON Schema for the TypeScript type generator (ADR-004)."""
    return _adapter.json_schema()
