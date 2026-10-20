"""The agent loop: user turns, model calls, tool calls, with the budget checked before every call.

`run` returns the trace (a list of validated events). It never raises for a bad model or a window
that cannot fit: those end the run with a recorded status and reason. Convention the ledger relies
on: a compaction event is written before the messages it adds.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

from ctxcheck.harness.tools import Tool, dispatch
from ctxcheck.harness.types import Message, ModelResponse, Origin, Role, ToolCall
from ctxcheck.policies.base import Policy, PolicyContext, PolicyError
from ctxcheck.providers.base import Provider
from ctxcheck.schema import (
    CanaryPlantedEvent,
    CompactionEvent,
    MessageEvent,
    ModelCallEvent,
    RunEndEvent,
    RunStartEvent,
    ToolCallEvent,
    ToolResultEvent,
    TraceEvent,
)
from ctxcheck.tokens import count


@dataclass(frozen=True)
class Scripted:
    """What the agent already did in a turn, replayed into the window without calling a model.

    Experiments script the history before the probe: it is recorded context, not something the
    model under test is asked to produce, so an episode costs about one live call, not one per turn.
    """

    exchanges: tuple[tuple[ToolCall, str], ...] = ()  # (the call the agent made, its output)
    reply: str = "Done."


@dataclass(frozen=True)
class Turn:
    text: str
    origin: Origin = "user"
    canary: tuple[str, str, str] | None = None  # (canary_id, canary_type, value)
    scripted: Scripted | None = None  # None means the model answers this turn live

    def __post_init__(self) -> None:
        if self.canary and self.canary[2] not in self.text:
            raise ValueError("a planted fact must appear verbatim in its message")


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    system: str
    turns: Sequence[Turn]


def _now() -> str:
    return datetime.now(UTC).isoformat()


def run(
    scenario: Scenario,
    provider: Provider,
    tools: Sequence[Tool],
    *,
    limit_tokens: int,
    policy: Policy | None = None,
    run_id: str = "run-001",
    seed: int = 0,
    params: dict[str, Any] | None = None,
    max_calls_per_turn: int = 8,
    trial_index: int = 0,
    count_fn: Callable[[str], int] = count,
    clock: Callable[[], str] = _now,
    provider_name: str = "scripted",
    model: str = "scripted",
) -> list[TraceEvent]:
    params = params or {}
    specs = [t.spec for t in tools]
    tools_tokens = count_fn(json.dumps([asdict(s) for s in specs], sort_keys=True))
    events: list[TraceEvent] = []
    window: list[Message] = []
    counter = 0

    def emit(factory: Callable[..., TraceEvent], **fields: Any) -> None:
        events.append(factory(run_id=run_id, seq=len(events), ts=clock(), **fields))

    def next_id() -> str:
        nonlocal counter
        counter += 1
        return f"m{counter:03d}"

    def emit_message(m: Message) -> None:
        emit(MessageEvent, type="message", message_id=m.id, step=m.step, role=m.role,
             content=m.content, tokens_est=m.tokens_est, origin=m.origin)

    def add(
        role: Role, origin: Origin, text: str, step: int, call_id: str | None = None, **detail: Any
    ) -> Message:
        m = Message(next_id(), role, text, origin, count_fn(text), step, call_id, **detail)
        window.append(m)
        emit_message(m)
        return m

    def total() -> int:
        return tools_tokens + sum(m.tokens_est for m in window)

    def finish(status: str, reason: str, calls: int, steps: int) -> list[TraceEvent]:
        emit(RunEndEvent, type="run_end", status=status, reason=reason,
             totals={"model_calls": calls, "summary_calls": summary_calls, "steps": steps,
                     "tokens_final": total()})
        return events

    summary_calls = 0

    def emit_model_call(response: ModelResponse, sent: Sequence[Message]) -> None:
        request_hash = hashlib.sha256(
            json.dumps([(m.role, m.content) for m in sent], sort_keys=True).encode()
        ).hexdigest()
        emit(ModelCallEvent, type="model_call", request_hash=request_hash,
             trial_index=trial_index, model_id_reported=response.model_id,
             input_tokens=response.input_tokens, output_tokens=response.output_tokens,
             cache_read_input_tokens=response.cache_read_input_tokens,
             cache_creation_input_tokens=response.cache_creation_input_tokens,
             cassette_hit=bool(response.extra.get("cassette_hit", False)), cost_usd=0.0)

    def record_policy_call(response: ModelResponse, sent: Sequence[Message]) -> None:
        nonlocal summary_calls
        summary_calls += 1
        emit_model_call(response, sent)

    def compact(step: int) -> bool:
        """Bring the window under the limit. Returns False if it cannot (run must end).

        Raises PolicyError when the policy itself fails; the caller ends the run with its code.
        """
        if total() <= limit_tokens:
            return True
        if policy is None:
            return False
        ctx = PolicyContext(step=step, new_id=next_id, count=count_fn, trial_index=trial_index,
                            provider=provider, params=params, record_call=record_policy_call)
        new = policy.apply(tuple(window), limit_tokens - tools_tokens, ctx)
        old_ids, new_ids = {m.id for m in window}, {m.id for m in new}
        added = [m for m in new if m.id not in old_ids]
        after = tools_tokens + sum(m.tokens_est for m in new)
        if after > limit_tokens:
            return False
        emit(CompactionEvent, type="compaction", policy=policy.name, trigger="budget",
             tokens_before=total(), tokens_after=after,
             kept_ids=[m.id for m in new if m.id in old_ids],
             dropped_ids=[m.id for m in window if m.id not in new_ids],
             added_ids=[m.id for m in added],
             summary_message_id=next((m.id for m in added if m.origin == "summary"), None),
             prompt_version=getattr(policy, "prompt_version", None))
        window[:] = new
        for m in added:  # after the compaction event: the ledger's ordering convention
            emit_message(m)
        return True

    emit(RunStartEvent, type="run_start", scenario_id=scenario.scenario_id, seed=seed,
         policy=policy.name if policy else "none", provider=provider_name, model=model,
         params={**params, "scripted_turns": sum(t.scripted is not None for t in scenario.turns)},
         limit_tokens=limit_tokens, tools_tokens_est=tools_tokens)
    add("system", "user", scenario.system, step=1)

    calls = 0
    for step, turn in enumerate(scenario.turns, start=1):
        planted = add("user", turn.origin, turn.text, step)
        if turn.canary:
            cid, ctype, value = turn.canary
            emit(CanaryPlantedEvent, type="canary_planted", canary_id=cid, canary_type=ctype,
                 message_id=planted.id, value=value)
        if turn.scripted is not None:
            for n, (past_call, output) in enumerate(turn.scripted.exchanges):
                call_id = f"s{step}-{n}"
                scripted_call = ToolCall(call_id, past_call.name, past_call.args)
                args_json = json.dumps(scripted_call.args, sort_keys=True)
                add("assistant", "assistant", f"[tool_call {scripted_call.name} {args_json}]",
                    step, call_id=call_id, tool_call=scripted_call)
                emit(ToolCallEvent, type="tool_call", call_id=call_id, name=scripted_call.name,
                     args=scripted_call.args)
                emit(ToolResultEvent, type="tool_result", call_id=call_id, result=output,
                     is_error=False)
                add("tool", "tool", output, step, call_id=call_id)
            add("assistant", "assistant", turn.scripted.reply, step)
            continue  # no compaction or model call: the window is only checked at a live call
        turn_calls = 0
        while True:
            try:
                fits = compact(step)
            except PolicyError as e:
                return finish("error", e.code, calls, step)
            if not fits:
                return finish("error", "budget_exceeded", calls, step)
            if turn_calls >= max_calls_per_turn:
                return finish("aborted", "max_calls", calls, step)
            response = provider.complete(tuple(window), specs, params, trial_index)
            calls += 1
            turn_calls += 1
            emit_model_call(response, window)

            call = response.tool_call
            if call is None:  # end_turn: the model is done with this user turn
                add("assistant", "assistant", response.text, step)
                break
            args_json = json.dumps(call.args, sort_keys=True)
            text = f"{response.text}\n[tool_call {call.name} {args_json}]"
            add("assistant", "assistant", text.strip(), step, call_id=call.id,
                tool_call=call, lead_in=response.text)
            emit(ToolCallEvent, type="tool_call", call_id=call.id, name=call.name, args=call.args)
            result, tool = dispatch(tools, call)
            emit(ToolResultEvent, type="tool_result", call_id=call.id, result=result.text,
                 is_error=result.is_error)
            add("tool", "tool", result.text, step, call_id=call.id, is_error=result.is_error)
            if tool is not None and tool.terminal and not result.is_error:
                return finish("ok", "terminal_tool", calls, step)

    return finish("ok", "end_turn", calls, len(scenario.turns))
