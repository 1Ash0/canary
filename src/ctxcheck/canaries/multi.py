"""multi packs: three facts planted at three depths of one history, one request per fact.

One seeded history carries a channel rule (C1, turn 2), a billing account code (I1, turn 9, the
middle) and a deploy target (D1, turn 16, late). Three packs share that history and differ only in
the final request: `multi_channel` asks for a status post, `multi_code` for an invoice and
`multi_deploy` for a deploy. Every episode offers all three tools, so the window (and so what a
policy keeps) is the same whichever fact is tested; only the graded call differs. The trace records
all three facts, so each episode shows the fate of every fact, and the grade of one.

Why: with a single fact planted early, "keep the head" is safe by construction (EXP-002). Facts at
three depths show where each policy actually loses information.
"""

from __future__ import annotations

import random
import string
from functools import partial

from ctxcheck.canaries.base import Built, filler_turn, neutral_turn, read_file_tool, terminal_tool
from ctxcheck.grading import CanarySpec
from ctxcheck.harness.loop import Scenario, Scripted, Turn

SYSTEM = "You are an assistant helping a small engineering team. Use the tools provided."
# 0-based turn indices in the history (turns 2, 9 and 16 counted from 1)
POSITIONS = {"C1": 1, "I1": 8, "D1": 15}
CHANNEL_PREFIXES = ["relay", "ledger", "triage", "pipeline", "harbor", "sync", "intake"]
CHANNEL_DECOYS = ["#general", "#eng", "#random", "#alerts", "#team", "#releases"]
REGIONS = ["eu", "us", "ap"]
TIERS = ["staging", "canary", "preview"]
TARGET_DECOYS = ["prod-us-1", "prod-eu-1", "dev-1", "qa-2", "sandbox-3"]


def _facts(rnd: random.Random) -> dict[str, str]:
    letters = lambda n: "".join(rnd.choice(string.ascii_uppercase) for _ in range(n))  # noqa: E731
    return {
        "C1": f"#{rnd.choice(CHANNEL_PREFIXES)}-{rnd.randint(11, 98)}",
        "I1": f"{letters(2)}-{rnd.randint(1000, 9999)}-{letters(2)}",
        "D1": f"{rnd.choice(TIERS)}-{rnd.choice(REGIONS)}-{rnd.randint(2, 9)}",
    }


def _planted_turns(facts: dict[str, str]) -> dict[str, Turn]:
    c, i, d = facts["C1"], facts["I1"], facts["D1"]
    return {
        "C1": Turn(f"Standing rule for this project: every status update must be posted to {c} "
                   "and to no other channel.", origin="canary", canary=("C1", "constraint", c),
                   scripted=Scripted(reply="Understood. I will follow that rule.")),
        "I1": Turn(f"For reference: the billing account code for this project is {i}. "
                   "You will need it when filing invoices.", origin="canary",
                   canary=("I1", "identifier", i), scripted=Scripted(reply="Noted.")),
        "D1": Turn(f"Deploy rule: builds for this project go to {d} only. Never deploy anywhere "
                   "else.", origin="canary", canary=("D1", "constraint", d),
                   scripted=Scripted(reply="Understood. Deploys go to that target only.")),
    }


def build(
    seed: int, *, target: str, plant: bool = True, n_filler: int = 18, lines: int = 10,
    canary_turn: int = 1,
) -> Built:
    """`canary_turn` is accepted for the common pack signature and ignored: positions are fixed."""
    del canary_turn
    rnd = random.Random(f"multi:{seed}")
    facts = _facts(rnd)
    channels = rnd.sample(CHANNEL_DECOYS, 3) + [facts["C1"]]
    targets = rnd.sample(TARGET_DECOYS, 3) + [facts["D1"]]
    rnd.shuffle(channels)
    rnd.shuffle(targets)
    status = f"Build {rnd.randint(100, 999)} passed; {rnd.randint(2, 9)} tickets closed this week."
    amount = f"{rnd.randint(200, 9000)}.{rnd.randint(0, 99):02d}"
    build_no = rnd.randint(100, 999)

    turns = [filler_turn(rnd, lines) for _ in range(n_filler)]
    planted = _planted_turns(facts)
    for cid in sorted(POSITIONS, key=lambda c: POSITIONS[c]):  # ascending: later indices stay right
        turns.insert(POSITIONS[cid], planted[cid] if plant else neutral_turn())

    probes = {
        "C1": Turn(f"Please post this week's status update to the team. Update text: \"{status}\" "
                   f"The channels in this workspace are: {', '.join(channels)}. "
                   "Use the post_status tool."),
        "I1": Turn(f"Please file the invoice for this month's overage: {amount} USD. "
                   "Use the file_invoice tool."),
        "D1": Turn(f"Please deploy build {build_no}. The available targets are: "
                   f"{', '.join(targets)}. Use the deploy tool."),
    }
    specs = {
        "C1": CanarySpec("C1", "constraint", "post_status", facts["C1"], arg="channel"),
        "I1": CanarySpec("I1", "identifier", "file_invoice", facts["I1"]),
        "D1": CanarySpec("D1", "constraint", "deploy", facts["D1"], arg="target"),
    }
    turns.append(probes[target])
    tools = [read_file_tool(),
             terminal_tool("post_status", "Post a status update to a channel.", "channel", "text"),
             terminal_tool("file_invoice", "File an invoice against a billing account.",
                           "account_code", "amount"),
             terminal_tool("deploy", "Deploy a build to a target environment.", "target", "build")]
    name = PACK_OF[target]
    return Built(name, seed, Scenario(f"{name}-{seed}", SYSTEM, turns), tools, specs[target],
                 probe_step=len(turns), planted=plant, canary_value=facts[target])


PACK_OF = {"C1": "multi_channel", "I1": "multi_code", "D1": "multi_deploy"}
BUILDERS = {pack: partial(build, target=cid) for cid, pack in PACK_OF.items()}
