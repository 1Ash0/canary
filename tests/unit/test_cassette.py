"""Cassettes: record, replay, auto; keys; trial independence; a miss never reaches the network."""

import json
from pathlib import Path

import pytest

from ctxcheck.harness.types import Message, ModelResponse, ToolCall, ToolSpec
from ctxcheck.providers.cassette import CassetteMiss, CassetteProvider, make_key, request_dict
from ctxcheck.providers.scripted import ScriptedProvider

TOOLS = [ToolSpec("read_file", "Read", {"type": "object", "properties": {}})]


def msg(content="hi", role="user", mid="m1", **kw) -> Message:
    return Message(mid, role, content, role, 1, 1, **kw)


class Counting:
    """A provider that counts calls, so tests can prove replays make none."""

    def __init__(self) -> None:
        self.calls = 0

    def complete(self, messages, tools, params, trial_index) -> ModelResponse:
        self.calls += 1
        return ModelResponse(text=f"reply {trial_index}", input_tokens=5, output_tokens=2,
                             model_id="m-1", extra={"stop_reason": "end_turn"})


def make(tmp_path: Path, mode, inner=None) -> CassetteProvider:
    return CassetteProvider(tmp_path, mode, inner=inner, provider_name="p", model="m")


def test_key_ignores_dict_order_and_is_stable() -> None:
    a = {"model": "m", "trial_index": 0, "messages": []}
    b = {"trial_index": 0, "messages": [], "model": "m"}
    assert make_key(a) == make_key(b) and len(make_key(a)) == 64


def test_trial_index_changes_the_key() -> None:
    base = request_dict("p", "m", [msg()], TOOLS, {}, 0)
    other = request_dict("p", "m", [msg()], TOOLS, {}, 1)
    assert make_key(base) != make_key(other)


def test_key_ignores_message_ids_and_bookkeeping_but_not_content() -> None:
    k1 = make_key(request_dict("p", "m", [msg(mid="m001")], TOOLS, {}, 0))
    k2 = make_key(request_dict("p", "m", [msg(mid="m999")], TOOLS, {}, 0))
    k3 = make_key(request_dict("p", "m", [msg("different")], TOOLS, {}, 0))
    assert k1 == k2 and k1 != k3


def test_key_depends_on_provider_model_params_and_tools() -> None:
    base = request_dict("p", "m", [msg()], TOOLS, {}, 0)
    for changed in (
        request_dict("q", "m", [msg()], TOOLS, {}, 0),
        request_dict("p", "n", [msg()], TOOLS, {}, 0),
        request_dict("p", "m", [msg()], TOOLS, {"temperature": 1.0}, 0),
        request_dict("p", "m", [msg()], [], {}, 0),
    ):
        assert make_key(changed) != make_key(base)


def test_record_writes_a_readable_cassette_and_replay_makes_no_call(tmp_path: Path) -> None:
    inner = Counting()
    first = make(tmp_path, "record", inner).complete([msg()], TOOLS, {}, 0)
    assert inner.calls == 1 and first.extra["cassette_hit"] is False
    files = list(tmp_path.glob("*.json"))
    assert len(files) == 1
    entry = json.loads(files[0].read_text(encoding="utf-8"))
    assert entry["response"]["text"] == "reply 0" and "meta" in entry
    assert entry["meta"]["recorded_at"] and "python" in entry["meta"]["versions"]

    replayed = make(tmp_path, "replay").complete([msg()], TOOLS, {}, 0)
    assert replayed.text == "reply 0" and replayed.extra["cassette_hit"] is True
    assert (replayed.input_tokens, replayed.output_tokens, replayed.model_id) == (5, 2, "m-1")
    assert inner.calls == 1  # replay never called the provider


def test_a_missing_cassette_raises_and_never_calls_anything(tmp_path: Path) -> None:
    inner = Counting()
    provider = make(tmp_path, "replay")
    with pytest.raises(CassetteMiss, match="cassette missing"):
        provider.complete([msg()], TOOLS, {}, 0)
    assert inner.calls == 0 and provider.misses == 1


def test_a_missing_cassette_error_is_a_file_not_found_error(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        make(tmp_path, "replay").complete([msg()], TOOLS, {}, 0)


def test_auto_records_once_then_replays(tmp_path: Path) -> None:
    inner = Counting()
    provider = make(tmp_path, "auto", inner)
    a = provider.complete([msg()], TOOLS, {}, 0)
    b = provider.complete([msg()], TOOLS, {}, 0)
    assert inner.calls == 1 and (provider.hits, provider.misses) == (1, 1)
    assert a.text == b.text and (a.extra["cassette_hit"], b.extra["cassette_hit"]) == (False, True)


def test_record_mode_overwrites_while_auto_never_does(tmp_path: Path) -> None:
    inner = Counting()
    make(tmp_path, "record", inner).complete([msg()], TOOLS, {}, 0)
    make(tmp_path, "record", inner).complete([msg()], TOOLS, {}, 0)
    assert inner.calls == 2
    make(tmp_path, "auto", inner).complete([msg()], TOOLS, {}, 0)
    assert inner.calls == 2


def test_each_trial_gets_its_own_recording(tmp_path: Path) -> None:
    inner = Counting()
    provider = make(tmp_path, "auto", inner)
    texts = [provider.complete([msg()], TOOLS, {}, t).text for t in range(3)]
    assert texts == ["reply 0", "reply 1", "reply 2"] and len(list(tmp_path.glob("*.json"))) == 3
    assert inner.calls == 3


def test_tool_calls_survive_the_round_trip(tmp_path: Path) -> None:
    reply = ModelResponse(text="x", tool_call=ToolCall("t1", "read_file", {"path": "a"}),
                          cache_read_input_tokens=7)
    make(tmp_path, "record", ScriptedProvider([reply])).complete([msg()], TOOLS, {}, 0)
    back = make(tmp_path, "replay").complete([msg()], TOOLS, {}, 0)
    assert back.tool_call == ToolCall("t1", "read_file", {"path": "a"})
    assert back.cache_read_input_tokens == 7 and back.cache_creation_input_tokens is None


def test_record_and_auto_need_an_inner_provider(tmp_path: Path) -> None:
    for mode in ("record", "auto"):
        with pytest.raises(ValueError, match="inner provider"):
            CassetteProvider(tmp_path, mode)  # type: ignore[arg-type]


def test_a_cassette_never_contains_the_request_headers_or_a_key(tmp_path: Path) -> None:
    make(tmp_path, "record", Counting()).complete([msg()], TOOLS, {}, 0)
    text = next(tmp_path.glob("*.json")).read_text(encoding="utf-8").lower()
    assert "authorization" not in text and "api-key" not in text and "x-api" not in text
