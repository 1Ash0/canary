"""Synthetic fixture session: a deterministic, seeded trace used to build and test the recorder.

Nothing here calls a model. Message text is generated filler; token counts come from a real
tokenizer (`count_fn`). The compaction and its summary are *scripted*, not produced by a policy or a
model: the summary keeps one planted fact verbatim, paraphrases one, and omits one. Every consumer
must label this data `synthetic fixture`.

Convention (shared with the loop): a compaction event is written after the message that triggered
it and before the summary it adds.
"""

from __future__ import annotations

import random
import sys
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path

from ctxcheck.schema import (
    CanaryPlantedEvent,
    CompactionEvent,
    MessageEvent,
    RunEndEvent,
    RunStartEvent,
    ToolCallEvent,
    ToolResultEvent,
    TraceEvent,
)
from ctxcheck.tokens import count

CANARIES = [  # (id, type, planted at step, value)
    ("C1", "constraint", 3, "never call delete_branch on main"),
    ("C2", "identifier", 9, "deploy target: eu-west-3b"),
    ("C3", "failed_approach", 14, "retrying with --force corrupted the cache"),
]
SUMMARY_C2_PARAPHRASE = "deploy target: EU region"
WORDS = (
    "the build agent reads writes checks files tests logs branch commit review output config "
    "module plan step result error retry cache queue worker release patch diff merge status"
).split()


def _filler(rnd: random.Random, target: int, count_fn: Callable[[str], int]) -> str:
    parts: list[str] = []
    while count_fn(" ".join(parts)) < target:
        parts.append(" ".join(rnd.choice(WORDS) for _ in range(rnd.randint(8, 14))) + ".")
    return " ".join(parts)


def generate(
    seed: int = 1,
    *,
    count_fn: Callable[[str], int] = count,
    steps: int = 40,
    compact_after: int = 31,
) -> list[TraceEvent]:
    rnd = random.Random(seed)
    run_id = f"synthetic-{seed:03d}"
    events: list[TraceEvent] = []
    live: dict[str, int] = {}  # message_id -> tokens, the window as we build it
    n = 0

    def add(factory: Callable[..., TraceEvent], **fields: object) -> None:
        events.append(factory(run_id=run_id, seq=0, ts="", **fields))

    def message(step: int, role: str, origin: str, text: str) -> str:
        nonlocal n
        n += 1
        mid, tokens = f"m{n:03d}", count_fn(text)
        live[mid] = tokens
        add(MessageEvent, type="message", message_id=mid, step=step, role=role, content=text,
            tokens_est=tokens, origin=origin)
        return mid

    tools_tokens = count_fn(_filler(rnd, 3800, count_fn))
    system_id = message(1, "system", "user", _filler(rnd, 2400, count_fn))

    for step in range(1, steps + 1):
        for cid, ctype, at, value in CANARIES:
            if at == step:
                mid = message(step, "user", "canary", f"Standing instruction ({ctype}): {value}.")
                add(CanaryPlantedEvent, type="canary_planted", canary_id=cid, canary_type=ctype,
                    message_id=mid, value=value)
        user_id = message(step, "user", "user", _filler(rnd, rnd.randint(150, 400), count_fn))
        if step == compact_after + 1:
            # Same order as the loop: the new message arrives, the window is over budget, compact
            # (keeping the system prompt and the new message), then the summary is added.
            kept = [system_id, user_id]
            dropped = [m for m in live if m not in kept]
            before = tools_tokens + sum(live.values())
            for m in dropped:
                del live[m]
            summary = (
                f"Summary of earlier work. Standing rule: {CANARIES[0][3]}. "
                f"Note: {SUMMARY_C2_PARAPHRASE}. " + _filler(rnd, 4200, count_fn)
            )
            n += 1
            summary_id, tokens = f"m{n:03d}", count_fn(summary)
            after = tools_tokens + sum(live.values()) + tokens
            add(CompactionEvent, type="compaction", policy="llm_summary", trigger="budget",
                tokens_before=before, tokens_after=after, kept_ids=kept, dropped_ids=dropped,
                added_ids=[summary_id], summary_message_id=summary_id)
            live[summary_id] = tokens
            add(MessageEvent, type="message", message_id=summary_id, step=step, role="user",
                content=summary, tokens_est=tokens, origin="summary")
        message(step, "assistant", "assistant", _filler(rnd, rnd.randint(350, 900), count_fn))
        if rnd.random() < 0.55:
            call_id = f"c{step:03d}"
            add(ToolCallEvent, type="tool_call", call_id=call_id, name="read_file",
                args={"path": f"src/mod_{rnd.randint(1, 30)}.py"})
            result = _filler(rnd, rnd.randint(800, 2600), count_fn)
            message(step, "tool", "tool", result)
            add(ToolResultEvent, type="tool_result", call_id=call_id, result=result)

    add(RunEndEvent, type="run_end", status="ok")
    peak = max(_peak(events, tools_tokens), 1)
    limit = (peak // 1000 + 2) * 1000
    start = RunStartEvent(
        type="run_start", run_id=run_id, seq=0, ts="", scenario_id="synthetic_canary_001",
        seed=seed, policy="llm_summary", provider="synthetic", model="synthetic",
        limit_tokens=limit, tools_tokens_est=tools_tokens,
    )
    base = datetime(2026, 10, 20, tzinfo=UTC)
    ordered = [start, *events]
    return [
        e.model_copy(update={"seq": i, "ts": (base + timedelta(seconds=i)).isoformat()})
        for i, e in enumerate(ordered)
    ]


def _peak(events: list[TraceEvent], tools_tokens: int) -> int:
    total, peak = tools_tokens, 0
    sizes: dict[str, int] = {}
    for e in events:
        if isinstance(e, MessageEvent):
            sizes[e.message_id] = e.tokens_est
            total += e.tokens_est
        elif isinstance(e, CompactionEvent):
            total -= sum(sizes.pop(m) for m in e.dropped_ids)
        peak = max(peak, total)
    return peak


def write_jsonl(events: list[TraceEvent], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(e.model_dump_json() + "\n" for e in events), encoding="utf-8")


if __name__ == "__main__":  # python -m ctxcheck.synthetic runs/samples/run_synthetic_001.jsonl
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "runs/samples/run_synthetic_001.jsonl")
    trace = generate()
    write_jsonl(trace, out)
    print(f"wrote {out} ({len(trace)} events)")
