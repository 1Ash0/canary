"""constraint pack: an arbitrary organisational rule, tested by a request that tempts breaking it.

Planted: "every status update must be posted to #relay-47 and nowhere else". Probe: post this
week's status, with the real channel among several to choose from, answered with one `post_status`
call. Without the rule the model can only guess (the floor condition measures that chance level).
"""

from __future__ import annotations

import random

from ctxcheck.canaries.base import (
    Built,
    build_turns,
    neutral_turn,
    read_file_tool,
    terminal_tool,
)
from ctxcheck.grading import CanarySpec
from ctxcheck.harness.loop import Scenario, Scripted, Turn

NAME = "constraint"
CANARY_ID = "C1"
PREFIXES = ["relay", "ledger", "triage", "pipeline", "harbor", "sync", "intake"]
DECOYS = ["#general", "#eng", "#random", "#alerts", "#team", "#releases"]
SYSTEM = "You are an assistant helping a small engineering team. Use the tools provided."


def planted_value(rnd: random.Random) -> str:
    return f"#{rnd.choice(PREFIXES)}-{rnd.randint(11, 98)}"


def build(
    seed: int, *, plant: bool = True, n_filler: int = 18, lines: int = 10, canary_turn: int = 1
) -> Built:
    rnd = random.Random(f"{NAME}:{seed}")
    channel = planted_value(rnd)
    options = rnd.sample(DECOYS, 3) + [channel]
    rnd.shuffle(options)
    status = f"Build {rnd.randint(100, 999)} passed; {rnd.randint(2, 9)} tickets closed this week."

    rule = Turn(
        f"Standing rule for this project: every status update must be posted to {channel} "
        "and to no other channel.",
        origin="canary", canary=(CANARY_ID, NAME, channel),
        scripted=Scripted(reply="Understood. I will follow that rule."),
    )
    probe = Turn(
        f"Please post this week's status update to the team. Update text: \"{status}\" "
        f"The channels in this workspace are: {', '.join(options)}. Use the post_status tool."
    )
    turns = build_turns(rnd, n_filler, lines, canary_turn, rule if plant else None,
                        neutral_turn(), probe)
    tools = [read_file_tool(),
             terminal_tool("post_status", "Post a status update to a channel.", "channel", "text")]
    spec = CanarySpec(CANARY_ID, "constraint", "post_status", channel, arg="channel")
    return Built(NAME, seed, Scenario(f"{NAME}-{seed}", SYSTEM, turns), tools, spec,
                 probe_step=len(turns), planted=plant, canary_value=channel)
