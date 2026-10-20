"""The five policy invariants (ARCHITECTURE §Policy invariants), checked on random windows.

1. The result fits the budget, or the policy raises IrreducibleBudget. Never a silent overrun.
2. A tool call is kept exactly when its result is kept.
3. Kept messages stay in their original order.
4. Deterministic policies are pure, and idempotent once the window fits.
5. Nothing disappears unrecorded: after every compaction event in a real run, kept + dropped is
   exactly the window before it.
"""

from itertools import count as counter

from hypothesis import given, settings
from hypothesis import strategies as st

from ctxcheck.harness.loop import Scenario, Turn, run
from ctxcheck.harness.tools import Tool
from ctxcheck.harness.types import Message, ModelResponse, ToolCall, ToolSpec
from ctxcheck.policies import DETERMINISTIC, IrreducibleBudget, PolicyContext, make_policy
from ctxcheck.providers.scripted import ScriptedProvider


def words(text: str) -> int:
    return len(text.split())


def fresh_ctx() -> PolicyContext:
    ids = counter(5000)
    return PolicyContext(step=9, new_id=lambda: f"n{next(ids)}", count=words)


def mk(i: int, role: str, n: int, call_id: str | None = None, call: bool = False) -> Message:
    origin = {"system": "user", "tool": "tool", "assistant": "assistant"}.get(role, role)
    tool_call = ToolCall(call_id or "", "read_file", {}) if call else None
    return Message(f"m{i:04d}", role, f"{role}{i} " + "w " * n, origin, n, 1,  # type: ignore[arg-type]
                   call_id=call_id, tool_call=tool_call)


@st.composite
def windows(draw) -> list[Message]:
    """system, any mix of history units, then a current turn that may include tool pairs."""
    out: list[Message] = [mk(0, "system", draw(st.integers(1, 20)))]
    i = 1
    for kind in draw(st.lists(st.sampled_from(["user", "assistant", "pair"]), max_size=12)):
        if kind == "pair":
            cid = f"c{i}"
            out.append(mk(i, "assistant", draw(st.integers(1, 10)), cid, call=True))
            out.append(mk(i + 1, "tool", draw(st.integers(1, 60)), cid))
            i += 2
        else:
            out.append(mk(i, kind, draw(st.integers(1, 30))))
            i += 1
    out.append(mk(i, "user", draw(st.integers(1, 20))))  # the current turn begins here
    i += 1
    if draw(st.booleans()):
        cid = f"c{i}"
        out.append(mk(i, "assistant", draw(st.integers(1, 10)), cid, call=True))
        out.append(mk(i + 1, "tool", draw(st.integers(1, 40)), cid))
    return out


def total(w: list[Message]) -> int:
    return sum(m.tokens_est for m in w)


def floor_of(w: list[Message]) -> int:
    last_user = max(i for i, m in enumerate(w) if m.role == "user")
    return w[0].tokens_est + total(w[last_user:])


budgets = st.integers(1, 400)
policy_names = st.sampled_from(DETERMINISTIC)


@given(windows(), budgets, policy_names)
@settings(max_examples=300, deadline=None)
def test_1_result_fits_the_budget_or_the_policy_says_it_cannot(w, budget, name) -> None:
    policy = make_policy(name)
    if total(w) > budget and floor_of(w) > budget:
        try:
            policy.apply(w, budget, fresh_ctx())
        except IrreducibleBudget:
            return
        raise AssertionError("should have raised IrreducibleBudget")
    out = policy.apply(w, budget, fresh_ctx())
    if total(w) <= budget:
        assert out == w  # already fits: nothing may change
    else:
        assert total(out) <= budget


@given(windows(), budgets, policy_names)
@settings(max_examples=300, deadline=None)
def test_2_a_call_is_kept_exactly_when_its_result_is(w, budget, name) -> None:
    try:
        out = make_policy(name).apply(w, budget, fresh_ctx())
    except IrreducibleBudget:
        return
    calls = {m.call_id for m in out if m.tool_call is not None}
    results = {m.call_id for m in out if m.role == "tool"}
    assert calls == results


@given(windows(), budgets, policy_names)
@settings(max_examples=300, deadline=None)
def test_3_kept_messages_keep_their_order(w, budget, name) -> None:
    try:
        out = make_policy(name).apply(w, budget, fresh_ctx())
    except IrreducibleBudget:
        return
    original = [m.id for m in w]
    # a masked output is a new message that takes the place of the one it replaced
    replaced = {m.id: i for i, m in enumerate(w)}
    positions = []
    for m in out:
        if m.id in replaced:
            positions.append(replaced[m.id])
        else:  # a mask: same call_id as the original it replaced
            positions.append(next(i for i, o in enumerate(w)
                                  if o.role == "tool" and o.call_id == m.call_id))
    assert positions == sorted(positions) and len(set(positions)) == len(positions)
    assert out[0].id == original[0]


@given(windows(), budgets, policy_names)
@settings(max_examples=300, deadline=None)
def test_4_pure_and_idempotent(w, budget, name) -> None:
    policy = make_policy(name)
    try:
        a = policy.apply(w, budget, fresh_ctx())
        b = policy.apply(w, budget, fresh_ctx())
    except IrreducibleBudget:
        return
    assert a == b  # pure: same input, same output, even down to the new message ids
    if total(a) <= budget:
        assert policy.apply(a, budget, fresh_ctx()) == a  # idempotent once it fits


READ = Tool(ToolSpec("read_file", "Read", {"type": "object", "properties": {}}),
            fn=lambda: "w " * 15)


@given(st.integers(2, 9), st.integers(4, 40), st.integers(40, 160), policy_names,
       st.booleans())
@settings(max_examples=120, deadline=None)
def test_5_compaction_events_account_for_every_message(n_turns, turn_words, limit, name,
                                                         use_tools) -> None:
    turns = [Turn("t " * turn_words + f"turn{i}") for i in range(n_turns)]
    replies: list[ModelResponse] = []
    for i in range(n_turns):
        if use_tools:
            replies.append(ModelResponse(tool_call=ToolCall(f"c{i}", "read_file", {})))
        replies.append(ModelResponse(text="done"))
    ticks = counter()
    events = run(Scenario("p", "You are an agent.", turns), ScriptedProvider(replies), [READ],
                 limit_tokens=limit, policy=make_policy(name), count_fn=words,
                 clock=lambda: f"2026-10-20T00:00:{next(ticks) % 60:02d}Z")
    live: set[str] = set()
    for e in events:
        if e.type == "message":
            live.add(e.message_id)
        elif e.type == "compaction":
            assert set(e.kept_ids) | set(e.dropped_ids) == live
            assert not set(e.kept_ids) & set(e.dropped_ids)
            assert e.tokens_after <= limit
            live = set(e.kept_ids)
