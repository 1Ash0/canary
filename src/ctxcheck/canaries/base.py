"""Shared pieces for canary packs: the built episode, seeded filler, and length-matching.

Design rules (EVAL_DESIGN §2): planted values are seed-generated, never famous; the probe holds
everything needed to act; the probe is answered with one terminal tool call; and every filler turn
is generated from the seed so a cell is reproducible. Filler never contains rule-like language or
anything shaped like a channel or an account code, so it cannot leak or imitate a canary.
"""

from __future__ import annotations

import random
from collections.abc import Callable
from dataclasses import dataclass, replace

from ctxcheck.grading import CanarySpec
from ctxcheck.harness.loop import Scenario, Scripted, Turn, run
from ctxcheck.harness.tools import Tool
from ctxcheck.harness.types import ToolCall, ToolSpec
from ctxcheck.providers.scripted import ScriptedProvider
from ctxcheck.tokens import count

MODULES = ["scheduler", "indexer", "exporter", "importer", "cache", "gateway", "parser", "renderer"]
VERBS = ["processed", "validated", "queued", "compacted", "flushed", "retried", "skipped"]
NOUNS = ["records", "batches", "entries", "segments", "requests", "files", "rows"]
TASKS = ["check what changed in", "look through", "summarise the state of", "scan", "review"]
FILES = ["config.yaml", "worker.py", "notes.md", "report.csv", "schema.sql", "queue.log",
         "metrics.json", "routes.py", "cleanup.sh", "tests.py"]


@dataclass(frozen=True)
class Built:
    pack: str
    seed: int
    scenario: Scenario
    tools: list[Tool]
    spec: CanarySpec
    probe_step: int  # the live turn; everything before it is scripted
    planted: bool
    canary_value: str  # the planted fact (also present in spec); kept even when not planted


def read_file_tool() -> Tool:
    spec = ToolSpec("read_file", "Read a file and return its contents.",
                    {"type": "object", "properties": {"path": {"type": "string"}},
                     "required": ["path"]})
    return Tool(spec, fn=lambda path: f"(contents of {path})")


def terminal_tool(name: str, description: str, *params: str) -> Tool:
    schema = {"type": "object", "properties": {p: {"type": "string"} for p in params},
              "required": list(params)}
    return Tool(ToolSpec(name, description, schema), fn=lambda **kw: "accepted", terminal=True)


def filler_turn(rnd: random.Random, lines: int) -> Turn:
    """One benign task: the user asks, the agent read a file, replied. All scripted."""
    path = rnd.choice(FILES)
    log = "\n".join(
        f"{rnd.randint(10, 23):02d}:{rnd.randint(0, 59):02d}:{rnd.randint(0, 59):02d} "
        f"{rnd.choice(MODULES)}.{rnd.choice(VERBS)} {rnd.randint(2, 900)} {rnd.choice(NOUNS)} "
        f"in {rnd.randint(3, 480)}ms"
        for _ in range(lines)
    )
    task = f"Please {rnd.choice(TASKS)} {path} and tell me anything odd."
    reply = (f"I read {path}. {rnd.choice(MODULES)} {rnd.choice(VERBS)} "
             f"{rnd.randint(2, 900)} {rnd.choice(NOUNS)}; nothing looks wrong.")
    call = ToolCall("tmp", "read_file", {"path": path})
    return Turn(task, scripted=Scripted(exchanges=((call, log),), reply=reply))


def build_turns(
    rnd: random.Random,
    n_filler: int,
    lines: int,
    canary_turn: int,
    plant: Turn | None,
    neutral: Turn,
    probe: Turn,
) -> list[Turn]:
    """Filler turns with the planted turn at `canary_turn` (a neutral turn when not planted)."""
    turns = [filler_turn(rnd, lines) for _ in range(n_filler)]
    insert = plant if plant is not None else neutral
    turns.insert(min(canary_turn, len(turns)), insert)
    turns.append(probe)
    return turns


def window_tokens_before_probe(built: Built, count_fn: Callable[[str], int] = count) -> int:
    """Tokens in the window just before the probe turn (tools and system prompt included)."""
    without_probe = replace(built.scenario, turns=built.scenario.turns[:-1])
    events = run(without_probe, ScriptedProvider([]), built.tools, limit_tokens=10**9,
                 count_fn=count_fn, clock=lambda: "t")
    end = events[-1]
    assert end.type == "run_end"
    probe_tokens = count_fn(built.scenario.turns[-1].text)
    return int(end.totals["tokens_final"]) + probe_tokens


def trim_to_length(
    built: Built, target_tokens: int, count_fn: Callable[[str], int] = count
) -> tuple[Built, int]:
    """Drop the oldest filler turns until the pre-probe window is no longer than the target.

    Never drops the planted turn, the neutral stand-in or the probe. Returns the trimmed episode
    and its actual length, which is at most the target unless even zero filler is too long.
    """
    turns = list(built.scenario.turns)
    planted_at = next((i for i, t in enumerate(turns) if t.canary or t.text == _NEUTRAL_MARK), -1)
    candidate = built
    while True:
        size = window_tokens_before_probe(candidate, count_fn)
        droppable = [i for i, t in enumerate(turns[:-1]) if i != planted_at and t.scripted]
        if size <= target_tokens or not droppable:
            return candidate, size
        drop = droppable[0]
        turns.pop(drop)
        if drop < planted_at:
            planted_at -= 1
        candidate = replace(candidate, scenario=replace(built.scenario, turns=list(turns)),
                            probe_step=len(turns))


# A neutral stand-in for the planted turn (floor condition) carries this exact text so trimming can
# recognise and keep it, which keeps floor and length-matched episodes comparable in shape.
_NEUTRAL_MARK = "Quick note: carry on with the next item when you are ready."


def neutral_turn() -> Turn:
    return Turn(_NEUTRAL_MARK, scripted=Scripted(reply="Understood."))
