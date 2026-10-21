"""multi packs: three facts at fixed depths of one shared history, one graded request per fact."""

import pytest

from ctxcheck.canaries import build_pack, trim_to_length
from ctxcheck.canaries.multi import PACK_OF, POSITIONS
from ctxcheck.grading import grade_trace
from ctxcheck.harness.loop import run
from ctxcheck.harness.types import ModelResponse, ToolCall
from ctxcheck.policies import make_policy
from ctxcheck.providers.scripted import ScriptedProvider
from ctxcheck.runner.episode import all_fates
from ctxcheck.schema import MessageEvent

PACKS = list(PACK_OF.values())


def planted(built):
    return {t.canary[0]: (i, t.canary[2]) for i, t in enumerate(built.scenario.turns) if t.canary}


@pytest.mark.parametrize("pack", PACKS)
def test_three_facts_at_fixed_depths(pack) -> None:
    facts = planted(build_pack(pack, 5))
    assert {cid: i for cid, (i, _) in facts.items()} == POSITIONS


def test_the_three_packs_share_one_history_and_differ_only_in_the_request() -> None:
    a, b, c = (build_pack(p, 5) for p in PACKS)
    assert a.scenario.turns[:-1] == b.scenario.turns[:-1] == c.scenario.turns[:-1]
    requests = {x.scenario.turns[-1].text for x in (a, b, c)}
    assert len(requests) == 3
    assert [t.spec.name for t in a.tools] == [t.spec.name for t in c.tools]  # same tool specs


@pytest.mark.parametrize("pack", PACKS)
def test_floor_plants_nothing_and_trimming_keeps_every_fact(pack) -> None:
    assert planted(build_pack(pack, 5, plant=False)) == {}
    trimmed, _ = trim_to_length(build_pack(pack, 5), 1200)
    assert set(planted(trimmed)) == {"C1", "I1", "D1"}


def answer(built, args, policy="head_tail"):
    reply = ModelResponse(tool_call=ToolCall("p", built.spec.tool_name, args))
    events = run(built.scenario, ScriptedProvider([reply]), built.tools, limit_tokens=2400,
                 policy=make_policy(policy), clock=lambda: "t")
    probe = next(e for e in events if isinstance(e, MessageEvent)
                 and e.step == built.probe_step and e.role == "user")
    return events, probe


def test_the_grade_reads_only_the_target_fact() -> None:
    built = build_pack("multi_deploy", 5)
    facts = {cid: v for cid, (_, v) in planted(built).items()}
    events, probe = answer(built, {"target": facts["D1"], "build": "1"})
    assert grade_trace(events, built.spec, after_seq=probe.seq).grade == "respected"
    events, probe = answer(built, {"target": facts["C1"], "build": "1"})  # another fact's value
    assert grade_trace(events, built.spec, after_seq=probe.seq).grade == "violated"


@pytest.mark.parametrize(("policy", "expected"), [
    ("head_tail", {"C1": "kept", "I1": "gone", "D1": "gone"}),
    ("recency_truncate", {"C1": "gone", "I1": "gone", "D1": "kept"}),
    ("observation_mask", {"C1": "kept", "I1": "kept", "D1": "kept"}),
])
def test_at_2400_each_policy_keeps_a_different_set_of_facts(policy, expected) -> None:
    built = build_pack("multi_code", 5)
    events, probe = answer(built, {"account_code": "x", "amount": "1"}, policy)
    assert all_fates(events, probe.message_id) == expected
