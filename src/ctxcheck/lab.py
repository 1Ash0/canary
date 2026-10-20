"""Data for the site's Compaction Lab: real scripted histories with exact token counts, and parity
cases that pin the browser's JS port of the deterministic policies to these Python policies.

The lab lets a reader move the rule, the budget and the policy and watch the window recompute.
For that to be honest the browser must compute exactly what `ctxcheck.policies` computes, so the
export carries every number the policies read (tokens per message, tool pairing, the token count
of each masked placeholder) and a fixed set of cases the design tests replay.
"""

from __future__ import annotations

from dataclasses import replace
from itertools import count as counter
from typing import Any

from ctxcheck.canaries import build_pack
from ctxcheck.harness.loop import run
from ctxcheck.harness.types import Message
from ctxcheck.policies import DETERMINISTIC, PolicyContext, make_policy
from ctxcheck.providers.scripted import ScriptedProvider
from ctxcheck.schema import MessageEvent
from ctxcheck.tokens import count

KIND = {"system": "system", "user": "history", "assistant": "history", "tool": "tool"}


def _window(seed: int, position: int, pack: str = "constraint") -> tuple[list[Message], int, Any]:
    """The window as the policy sees it at the probe: system, every turn, then the probe."""
    built = build_pack(pack, seed, canary_turn=position)
    history = replace(built.scenario, turns=built.scenario.turns[:-1])
    events = run(history, ScriptedProvider([]), built.tools, limit_tokens=10**9, clock=lambda: "t")
    tools_tokens = events[0].tools_tokens_est  # type: ignore[union-attr]
    msgs = []
    for e in events:
        if isinstance(e, MessageEvent):
            call = e.role == "assistant" and e.content.startswith("[tool_call")
            msgs.append(Message(e.message_id, e.role, e.content, e.origin, e.tokens_est, e.step,
                                call_id=f"c{e.step}" if call or e.role == "tool" else None,
                                tool_call=_marker() if call else None))
    probe = built.scenario.turns[-1].text
    msgs.append(Message("probe", "user", probe, "user", count(probe), len(built.scenario.turns)))
    return msgs, tools_tokens, built


def _marker():
    from ctxcheck.harness.types import ToolCall
    return ToolCall("x", "read_file", {})


def _placeholder_tokens(m: Message) -> int:
    return count(f"[tool output omitted: {m.tokens_est} tokens]")


def lab_history(seed: int, pack: str = "constraint") -> dict[str, Any]:
    """One seed's history, grouped by turn so the browser can move the rule turn anywhere."""
    msgs, tools_tokens, built = _window(seed, 1, pack)
    system, probe = msgs[0], msgs[-1]
    turns: dict[int, list[dict[str, Any]]] = {}
    for m in msgs[1:-1]:
        turns.setdefault(m.step, []).append({
            "role": m.role, "kind": "rule" if m.origin == "canary" else KIND[m.role],
            "tokens": m.tokens_est, "call": m.tool_call is not None,
            "masked": _placeholder_tokens(m) if m.role == "tool" else None,
            "text": m.content[:160],
        })
    ordered = [turns[k] for k in sorted(turns)]
    rule_at = next(i for i, t in enumerate(ordered) if any(x["kind"] == "rule" for x in t))
    rule_turn = ordered.pop(rule_at)
    return {
        "seed": seed, "pack": pack, "tools_tokens": tools_tokens,
        "system": {"tokens": system.tokens_est, "text": system.content[:160]},
        "rule": rule_turn, "filler": ordered,
        "probe": {"tokens": probe.tokens_est, "text": probe.content},
        "value": built.canary_value,
    }


def parity_cases(seeds: range, positions: tuple[int, ...], budgets: tuple[int, ...]) -> list[dict]:
    """What the Python policies keep for each (seed, position, budget, policy): indices into the
    window [system, *turn messages in order, probe], and which tool outputs were masked."""
    cases = []
    for seed in seeds:
        for position in positions:
            msgs, tools_tokens, _ = _window(seed, position)
            index = {m.id: i for i, m in enumerate(msgs)}
            total = tools_tokens + sum(m.tokens_est for m in msgs)
            for limit in budgets:
                for name in DETERMINISTIC:
                    ids = counter(10_000)
                    ctx = PolicyContext(step=99, new_id=lambda: f"n{next(ids)}", count=count)
                    if total <= limit:
                        out = msgs
                    else:
                        out = make_policy(name).apply(msgs, limit - tools_tokens, ctx)
                    kept = [index[m.id] for m in out if m.id in index]
                    masked = [i for i, m in enumerate(msgs) if m.role == "tool"
                              and any(o.id not in index and o.call_id == m.call_id for o in out)]
                    cases.append({"seed": seed, "position": position, "limit": limit,
                                  "policy": name, "kept": kept, "masked": masked,
                                  "tokens_after": tools_tokens + sum(o.tokens_est for o in out)})
    return cases
