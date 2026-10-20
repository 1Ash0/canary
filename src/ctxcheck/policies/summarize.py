"""llm_summary: replace older history with a model-written summary.

The compaction prompt is an explicit, versioned artifact (ARCHITECTURE §Security). It is built from
`PROMPTS[version]`, logged on the compaction event as `prompt_version`, and is part of the request
the cassette hashes, so a changed prompt can never replay an old recording.

v1 is deliberately generic: it does not tell the model to keep rules or identifiers. That is what a
default summarizer looks like and is the condition the preregistered hypotheses are about. v2 names
what to keep; it is a sensitivity check, not the baseline.

The summarizer reads tool outputs and user text verbatim, so text planted there reaches a second
model unfiltered. Treat the summary as untrusted output.
"""

from __future__ import annotations

from collections.abc import Sequence

from ctxcheck.harness.types import Message
from ctxcheck.policies.base import PolicyContext, SummaryFailed
from ctxcheck.policies.units import check_reducible, split, tokens
from ctxcheck.providers._http import ProviderError

PROMPTS: dict[str, str] = {
    "v1": (
        "Summarize the conversation below so that the work can continue from the summary alone. "
        "Be concise. Output only the summary."
    ),
    "v2": (
        "Summarize the conversation below so that the work can continue from the summary alone. "
        "Keep every instruction the user gave about how to act, and every exact name, "
        "identifier and number that may be needed later. Be concise. Output only the summary."
    ),
}


def _transcript(units: Sequence[list[Message]]) -> str:
    return "\n".join(f"[{m.role}] {m.content}" for u in units for m in u)


class LLMSummary:
    name = "llm_summary"

    def __init__(
        self,
        prompt_version: str = "v1",
        keep_units: int = 2,
        max_summary_tokens: int = 400,
    ) -> None:
        if prompt_version not in PROMPTS:
            raise ValueError(f"unknown prompt version {prompt_version!r}; known: {sorted(PROMPTS)}")
        self.prompt_version = prompt_version
        self.keep_units = keep_units
        self.max_summary_tokens = max_summary_tokens

    def apply(
        self, window: Sequence[Message], budget_tokens: int, ctx: PolicyContext
    ) -> list[Message]:
        if tokens(window) <= budget_tokens:
            return list(window)
        parts = split(window)
        check_reducible(parts, budget_tokens)
        if ctx.provider is None:
            raise SummaryFailed("llm_summary needs a provider in the policy context")
        cut = max(0, len(parts.units) - self.keep_units)
        old, recent = parts.units[:cut], parts.units[cut:]
        if not old:  # nothing older than the units we keep: nothing to summarise
            return list(window)

        prompt = PROMPTS[self.prompt_version]
        request = [
            Message("summary-prompt", "system", prompt, "user", ctx.count(prompt), ctx.step),
            Message("summary-input", "user", _transcript(old), "user",
                    ctx.count(_transcript(old)), ctx.step),
        ]
        params = {**ctx.params, "max_tokens": self.max_summary_tokens}
        try:
            response = ctx.provider.complete(request, [], params, ctx.trial_index)
        except ProviderError as e:
            # a 4xx other than 429 means the provider rejected this request (for example the model
            # tried to call a tool when none were offered): that is the summarizer failing, so the
            # episode records it. Rate limits and server errors are infrastructure and propagate.
            if e.status is not None and 400 <= e.status < 500 and e.status != 429:
                raise SummaryFailed(f"the summarizer request was rejected: {e}") from e
            raise
        if ctx.record_call is not None:
            ctx.record_call(response, request)
        text = response.text.strip()
        if not text:
            raise SummaryFailed("the summarizer returned no text")

        content = f"[Summary of earlier conversation]\n{text}"
        summary = Message(ctx.new_id(), "user", content, "summary", ctx.count(content), ctx.step)
        return [*parts.system, summary, *(m for u in recent for m in u), *parts.tail]
