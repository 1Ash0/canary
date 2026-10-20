"""Two-sided tests: valid lines must parse to the right class; invalid lines must be rejected."""

import json

import pytest
from pydantic import ValidationError

from ctxcheck.schema import (
    CanaryPlantedEvent,
    CompactionEvent,
    MessageEvent,
    RunEndEvent,
    RunStartEvent,
    event_json_schema,
    parse_event,
)

COMMON = {"schema_version": "0.1", "run_id": "r1", "seq": 0, "ts": "2026-10-20T00:00:00Z"}

VALID: dict[str, dict] = {
    "run_start": {
        "scenario_id": "s", "seed": 1, "policy": "recency_truncate", "provider": "anthropic",
        "model": "m", "limit_tokens": 64000, "tools_tokens_est": 3800,
    },
    "message": {
        "message_id": "m1", "step": 1, "role": "user", "content": "hi", "tokens_est": 2,
        "origin": "user",
    },
    "model_call": {
        "request_hash": "abc", "trial_index": 0, "model_id_reported": "m", "input_tokens": 10,
        "output_tokens": 5, "cassette_hit": True, "cost_usd": 0.0,
    },
    "tool_call": {"call_id": "c1", "name": "post", "args": {"channel": "#ops-7"}},
    "tool_result": {"call_id": "c1", "result": "ok"},
    "compaction": {
        "policy": "recency_truncate", "trigger": "budget", "tokens_before": 100,
        "tokens_after": 50, "kept_ids": ["m2"], "dropped_ids": ["m1"], "added_ids": [],
    },
    "canary_planted": {
        "canary_id": "C1", "canary_type": "constraint", "message_id": "m1", "value": "use #ops-7",
    },
    "canary_probe": {
        "canary_id": "C1", "probe_message_id": "m9", "grade": "violated", "evidence": "#general",
    },
    "run_end": {"status": "ok"},
}


def line(type_: str, **overrides) -> str:
    return json.dumps({**COMMON, "type": type_, **VALID[type_], **overrides})


@pytest.mark.parametrize("type_", VALID)
def test_every_event_type_round_trips(type_: str) -> None:
    event = parse_event(line(type_))
    assert event.type == type_
    assert parse_event(event.model_dump_json()) == event


def test_discriminator_picks_the_right_class() -> None:
    assert isinstance(parse_event(line("run_start")), RunStartEvent)
    assert isinstance(parse_event(line("message")), MessageEvent)
    assert isinstance(parse_event(line("compaction")), CompactionEvent)
    assert isinstance(parse_event(line("canary_planted")), CanaryPlantedEvent)
    assert isinstance(parse_event(line("run_end")), RunEndEvent)


def test_unknown_type_is_rejected() -> None:
    with pytest.raises(ValidationError, match="union_tag_invalid"):
        parse_event(json.dumps({**COMMON, "type": "teleport"}))


def test_missing_type_is_rejected() -> None:
    with pytest.raises(ValidationError, match="union_tag_not_found"):
        parse_event(json.dumps(COMMON))


def test_missing_required_field_is_rejected() -> None:
    fields = {k: v for k, v in VALID["message"].items() if k != "step"}
    bad = {**COMMON, "type": "message", **fields}
    with pytest.raises(ValidationError, match="step"):
        parse_event(json.dumps(bad))


def test_wrong_type_is_rejected() -> None:
    with pytest.raises(ValidationError):
        parse_event(line("message", tokens_est="many"))


def test_misspelled_field_is_rejected_not_dropped() -> None:
    with pytest.raises(ValidationError, match="extra_forbidden"):
        parse_event(line("message", tokens_etc=3))


@pytest.mark.parametrize(
    ("type_", "field", "value"),
    [
        ("message", "step", 0),
        ("message", "role", "narrator"),
        ("run_start", "limit_tokens", 0),
        ("canary_probe", "grade", "maybe"),
        ("run_end", "status", "done"),
    ],
)
def test_out_of_range_values_are_rejected(type_: str, field: str, value: object) -> None:
    with pytest.raises(ValidationError):
        parse_event(line(type_, **{field: value}))


def test_negative_seq_is_rejected() -> None:
    with pytest.raises(ValidationError):
        parse_event(line("run_end", seq=-1))


def test_json_schema_lists_every_event_type() -> None:
    schema = json.dumps(event_json_schema())
    for type_ in VALID:
        assert f'"{type_}"' in schema


def test_schema_0_1_traces_without_reason_still_parse() -> None:
    event = parse_event(line("run_end"))  # no `reason`: a 0.1-era line
    assert event.type == "run_end" and event.reason is None  # type: ignore[union-attr]


def test_run_end_accepts_an_optional_reason() -> None:
    event = parse_event(line("run_end", reason="terminal_tool"))
    assert event.reason == "terminal_tool"  # type: ignore[union-attr]


def test_new_events_are_written_as_schema_0_2() -> None:
    event = RunEndEvent(type="run_end", run_id="r", seq=0, ts="t", status="ok")
    assert event.schema_version == "0.2"
