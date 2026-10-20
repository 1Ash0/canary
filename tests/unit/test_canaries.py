"""Canary packs: seeded, defeat priors, leak nothing, and length-matching really matches."""

import re
from dataclasses import replace

import pytest

from ctxcheck.canaries import build_pack, trim_to_length, window_tokens_before_probe
from ctxcheck.harness.loop import run
from ctxcheck.providers.scripted import ScriptedProvider

PACKS = ["constraint", "identifier"]


@pytest.mark.parametrize("pack", PACKS)
def test_the_same_seed_builds_the_same_episode(pack: str) -> None:
    a, b = build_pack(pack, 7), build_pack(pack, 7)
    assert (a.scenario, a.spec, a.canary_value) == (b.scenario, b.spec, b.canary_value)
    assert [t.spec for t in a.tools] == [t.spec for t in b.tools]  # tool functions are lambdas


@pytest.mark.parametrize("pack", PACKS)
def test_different_seeds_plant_different_values(pack: str) -> None:
    values = {build_pack(pack, s).canary_value for s in range(30)}
    assert len(values) >= 25  # random strings, not a famous fixed value


@pytest.mark.parametrize("pack", PACKS)
def test_the_planted_value_appears_only_in_the_planted_turn_and_the_spec(pack: str) -> None:
    b = build_pack(pack, 3)
    carriers = [t for t in b.scenario.turns if b.canary_value in t.text]
    # the constraint probe lists the real channel so it is answerable; the code never appears
    expected = [True, False] if pack == "constraint" else [True]
    assert [t.canary is not None for t in carriers] == expected
    filler = [t for t in b.scenario.turns[:-1] if t.canary is None]
    for t in filler:
        assert b.canary_value not in t.text
        for call, output in t.scripted.exchanges if t.scripted else ():
            assert b.canary_value not in output and b.canary_value not in str(call.args)


@pytest.mark.parametrize("pack", PACKS)
def test_floor_plants_nothing_and_keeps_the_same_number_of_turns(pack: str) -> None:
    planted, floor = build_pack(pack, 3), build_pack(pack, 3, plant=False)
    assert not any(t.canary for t in floor.scenario.turns) and not floor.planted
    assert len(planted.scenario.turns) == len(floor.scenario.turns)
    assert all(b.canary_value not in t.text for b in [floor] for t in b.scenario.turns[:-1])


@pytest.mark.parametrize("pack", PACKS)
def test_history_is_scripted_and_only_the_probe_is_live(pack: str) -> None:
    b = build_pack(pack, 1)
    assert all(t.scripted is not None for t in b.scenario.turns[:-1])
    assert b.scenario.turns[-1].scripted is None and b.probe_step == len(b.scenario.turns)


def test_the_constraint_probe_lists_the_real_channel_among_the_options() -> None:
    b = build_pack("constraint", 5)
    probe = b.scenario.turns[-1].text
    assert b.canary_value in probe and len(re.findall(r"#[\w-]+", probe)) == 4


def test_the_identifier_probe_does_not_contain_the_code() -> None:
    b = build_pack("identifier", 5)
    assert b.canary_value not in b.scenario.turns[-1].text


def test_the_terminal_tool_is_the_one_the_grader_watches() -> None:
    for pack in PACKS:
        b = build_pack(pack, 2)
        terminal = [t for t in b.tools if t.terminal]
        assert [t.spec.name for t in terminal] == [b.spec.tool_name]


def test_unknown_pack_names_the_known_ones() -> None:
    with pytest.raises(ValueError, match="constraint"):
        build_pack("nope", 1)


def test_the_window_is_large_enough_to_force_compaction_at_the_default_limit() -> None:
    assert window_tokens_before_probe(build_pack("constraint", 1)) > 2400


def test_scripted_history_makes_no_model_calls_before_the_probe() -> None:
    b = build_pack("constraint", 1)
    history = replace(b.scenario, turns=b.scenario.turns[:-1])
    events = run(history, ScriptedProvider([]), b.tools, limit_tokens=10**7, clock=lambda: "t")
    assert not any(e.type == "model_call" for e in events) and events[-1].reason == "end_turn"


@pytest.mark.parametrize("pack", PACKS)
def test_length_matching_trims_filler_to_the_target_and_keeps_the_canary(pack: str) -> None:
    b = build_pack(pack, 4)
    full = window_tokens_before_probe(b)
    target = full - 1500
    trimmed, size = trim_to_length(b, target)
    assert size <= target and size > target - 600  # within about one filler turn
    assert any(t.canary for t in trimmed.scenario.turns)  # the canary was never trimmed
    assert trimmed.scenario.turns[-1] == b.scenario.turns[-1]  # nor the probe
    assert len(trimmed.scenario.turns) < len(b.scenario.turns)
    assert window_tokens_before_probe(trimmed) == size


def test_length_matching_a_floor_episode_keeps_its_neutral_stand_in() -> None:
    f = build_pack("constraint", 4, plant=False)
    trimmed, _ = trim_to_length(f, window_tokens_before_probe(f) - 1500)
    assert any("carry on" in t.text for t in trimmed.scenario.turns)


def test_length_matching_to_a_larger_target_changes_nothing() -> None:
    b = build_pack("constraint", 4)
    trimmed, size = trim_to_length(b, 10**6)
    assert trimmed.scenario == b.scenario and size == window_tokens_before_probe(b)
