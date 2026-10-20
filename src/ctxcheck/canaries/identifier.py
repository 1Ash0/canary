"""identifier pack: an exact value the agent must reuse later.

Planted: "the billing account code for this project is QX-4471-ZT". Probe: file an invoice, answered
with one `file_invoice` call. Graded correct only if the exact code appears in the call's arguments.
Without the code the model has nothing to copy (the floor condition measures guessing).
"""

from __future__ import annotations

import random
import string

from ctxcheck.canaries.base import (
    Built,
    build_turns,
    neutral_turn,
    read_file_tool,
    terminal_tool,
)
from ctxcheck.grading import CanarySpec
from ctxcheck.harness.loop import Scenario, Scripted, Turn

NAME = "identifier"
CANARY_ID = "I1"
SYSTEM = "You are an assistant helping a small finance team. Use the tools provided."


def planted_value(rnd: random.Random) -> str:
    def letters(n: int) -> str:
        return "".join(rnd.choice(string.ascii_uppercase) for _ in range(n))

    return f"{letters(2)}-{rnd.randint(1000, 9999)}-{letters(2)}"


def build(
    seed: int, *, plant: bool = True, n_filler: int = 18, lines: int = 10, canary_turn: int = 1
) -> Built:
    rnd = random.Random(f"{NAME}:{seed}")
    code = planted_value(rnd)
    amount = f"{rnd.randint(200, 9000)}.{rnd.randint(0, 99):02d}"

    note = Turn(
        f"For reference: the billing account code for this project is {code}. "
        "You will need it when filing invoices.",
        origin="canary", canary=(CANARY_ID, NAME, code),
        scripted=Scripted(reply="Noted."),
    )
    probe = Turn(f"Please file the invoice for this month's overage: {amount} USD. "
                 "Use the file_invoice tool.")
    turns = build_turns(rnd, n_filler, lines, canary_turn, note if plant else None,
                        neutral_turn(), probe)
    tools = [read_file_tool(),
             terminal_tool("file_invoice", "File an invoice against a billing account.",
                           "account_code", "amount")]
    spec = CanarySpec(CANARY_ID, "identifier", "file_invoice", code)
    return Built(NAME, seed, Scenario(f"{NAME}-{seed}", SYSTEM, turns), tools, spec,
                 probe_step=len(turns), planted=plant, canary_value=code)
