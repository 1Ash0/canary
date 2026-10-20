"""A toy agent that follows a rule only if it can still read it. Nothing it produces is measured.

It exists to exercise the whole pipeline (packs, policies, grader, stats, export, site) offline
and for free. It reads the window with regular expressions, so it follows a planted rule exactly
when the rule survived compaction verbatim, which is the question the real experiment asks of
real models. Rows it produces carry `source: "simulated"` and must be labelled so everywhere
they are shown.
"""

from __future__ import annotations

import hashlib
import random
import re
import string
from collections.abc import Sequence
from typing import Any

from ctxcheck.harness.types import Message, ModelResponse, ToolCall, ToolSpec
from ctxcheck.tokens import count

MODEL_ID = "simulated-agent-v1"
RULE = re.compile(r"[^.\n]*must be posted to (#[\w-]+)[^.\n]*\.")
CODE = re.compile(
    r"[^.\n]*billing account code for this project is "
    r"([A-Z]{2}-\d{4}-[A-Z]{2})[^.\n]*\."
)
OPTIONS = re.compile(r"channels in this workspace are: (.*?)\. Use")


class SimulatedAgent:
    simulated = True

    def __init__(self, p_follow: float = 0.95, p_keep_in_summary: float = 0.5, seed: int = 0):
        self.p_follow = p_follow
        self.p_keep = p_keep_in_summary
        self.seed = seed

    def _rng(self, messages: Sequence[Message], trial_index: int) -> random.Random:
        digest = hashlib.sha256(
            f"{self.seed}|{trial_index}|{messages[-1].content}".encode()
        ).hexdigest()
        return random.Random(digest)

    def complete(
        self,
        messages: Sequence[Message],
        tools: Sequence[ToolSpec],
        params: dict[str, Any],
        trial_index: int,
    ) -> ModelResponse:
        rnd = self._rng(messages, trial_index)
        tokens_in = sum(count(m.content) for m in messages)
        if not tools:  # a summarisation request: keep the rule sentence or lose it by chance
            found = RULE.search(messages[-1].content) or CODE.search(messages[-1].content)
            if found and rnd.random() < self.p_keep:
                text = f"The user reviewed several files. {found.group(0).strip()}"
            else:
                text = "The user asked for several files to be reviewed; nothing was wrong."
            return ModelResponse(text=text, input_tokens=tokens_in, output_tokens=count(text),
                                 model_id=MODEL_ID)

        earlier = "\n".join(m.content for m in messages[:-1] if m.role != "system")
        probe = messages[-1].content
        names = {t.name for t in tools}
        follow = rnd.random() < self.p_follow
        if "post_status" in names:
            rule = RULE.search(earlier)
            listed = OPTIONS.search(probe)
            options = listed.group(1).split(", ") if listed else ["#general"]
            channel = rule.group(1) if rule and follow else rnd.choice(options)
            args = {"channel": channel, "text": "Weekly status."}
            name = "post_status"
        else:
            code = CODE.search(earlier)
            guess = "".join(rnd.choice(string.ascii_uppercase) for _ in range(2)) \
                + f"-{rnd.randint(1000, 9999)}-" \
                + "".join(rnd.choice(string.ascii_uppercase) for _ in range(2))
            args = {"account_code": code.group(1) if code and follow else guess, "amount": "1.00"}
            name = "file_invoice"
        return ModelResponse(tool_call=ToolCall(f"sim-{trial_index}", name, args),
                             input_tokens=tokens_in, output_tokens=20, model_id=MODEL_ID)
