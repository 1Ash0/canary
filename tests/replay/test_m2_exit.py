"""M2 exit: record a run through the cassette layer, replay it offline, get the same trace.

The two traces may differ in exactly one field, `cassette_hit` (recorded=False, replayed=True), and
that difference is the proof the replay did not touch the provider.
"""

from itertools import count as counter
from pathlib import Path

from ctxcheck.harness.loop import Scenario, Turn, run
from ctxcheck.harness.tools import Tool
from ctxcheck.harness.types import ModelResponse, ToolCall, ToolSpec
from ctxcheck.providers.cassette import CassetteProvider
from ctxcheck.providers.scripted import ScriptedProvider
from ctxcheck.runner.trace_io import read_trace, write_trace


def words(text: str) -> int:
    return len(text.split())


def clock():
    ticks = counter()
    return lambda: f"2026-10-20T00:00:{next(ticks):02d}Z"


def _tool(name: str, prop: str, fn, terminal: bool = False) -> Tool:
    schema = {"type": "object", "properties": {prop: {"type": "string"}}, "required": [prop]}
    return Tool(ToolSpec(name, name, schema), fn=fn, terminal=terminal)


TOOLS = [
    _tool("read_file", "path", lambda path: f"contents {path}"),
    _tool("post", "text", lambda text: "posted", terminal=True),
]
SCENARIO = Scenario("m2", "You are an agent.", [Turn("Check a.py then post the result.")])
REPLIES = [
    ModelResponse(tool_call=ToolCall("c1", "read_file", {"path": "a.py"}), input_tokens=30,
                  output_tokens=8, model_id="scripted-1"),
    ModelResponse(tool_call=ToolCall("c2", "post", {"text": "ok"}), input_tokens=40,
                  output_tokens=6, model_id="scripted-1"),
]


def go(cassettes: Path, mode: str, inner=None):
    provider = CassetteProvider(cassettes, mode, inner=inner, provider_name="scripted",  # type: ignore[arg-type]
                                model="scripted-1")
    trace = run(SCENARIO, provider, TOOLS, limit_tokens=10_000, count_fn=words, clock=clock(),
                provider_name="scripted", model="scripted-1")
    return trace, provider


def test_replay_reproduces_the_recorded_trace_byte_for_byte_except_cassette_hit(
    tmp_path: Path,
) -> None:
    cassettes = tmp_path / "cassettes"
    recorded, rec = go(cassettes, "record", ScriptedProvider(REPLIES))
    replayed, rep = go(cassettes, "replay")
    write_trace(tmp_path / "a.jsonl", recorded)
    write_trace(tmp_path / "b.jsonl", replayed)

    a = (tmp_path / "a.jsonl").read_text(encoding="utf-8")
    b = (tmp_path / "b.jsonl").read_text(encoding="utf-8")
    assert a.replace('"cassette_hit":false', '"cassette_hit":true') == b
    assert (rec.hits, rec.misses, rep.hits, rep.misses) == (0, 2, 2, 0)


def test_replaying_twice_is_byte_identical(tmp_path: Path) -> None:
    cassettes = tmp_path / "cassettes"
    go(cassettes, "record", ScriptedProvider(REPLIES))
    write_trace(tmp_path / "1.jsonl", go(cassettes, "replay")[0])
    write_trace(tmp_path / "2.jsonl", go(cassettes, "replay")[0])
    assert (tmp_path / "1.jsonl").read_bytes() == (tmp_path / "2.jsonl").read_bytes()


def test_a_written_trace_reads_back_to_equal_events(tmp_path: Path) -> None:
    trace, _ = go(tmp_path / "c", "record", ScriptedProvider(REPLIES))
    write_trace(tmp_path / "t.jsonl", trace)
    assert read_trace(tmp_path / "t.jsonl") == trace


def test_the_replayed_trace_records_what_the_model_reported(tmp_path: Path) -> None:
    cassettes = tmp_path / "cassettes"
    go(cassettes, "record", ScriptedProvider(REPLIES))
    trace, _ = go(cassettes, "replay")
    calls = [e for e in trace if e.type == "model_call"]
    assert [(c.input_tokens, c.output_tokens, c.model_id_reported) for c in calls] == [
        (30, 8, "scripted-1"), (40, 6, "scripted-1")
    ]
    assert all(c.cassette_hit for c in calls)
