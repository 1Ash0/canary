"""
learn/tokens.py — U0 token ledger

Run:  uv run python learn/tokens.py

What this shows:
  1. How tiktoken counts tokens in a string (local estimate, NOT Anthropic's tokenizer)
  2. A token ledger for a short fake conversation: role / text / local_estimate / running_total
  3. How to read the three provider usage fields (from a real API response)
  4. The gap you'd measure between local_estimate and provider_reported

tiktoken uses cl100k_base (GPT-4 family). Claude uses a different tokenizer —
some model families count ~30% more tokens. This is a proxy; always verify with
the Anthropic count_tokens endpoint before making budget decisions in production.
"""

from __future__ import annotations

import tiktoken

# ── tokenizer ──────────────────────────────────────────────────────────────

ENCODING_NAME = "cl100k_base"  # GPT-4 family proxy; not Anthropic's tokenizer

def count(text: str) -> int:
    enc = tiktoken.get_encoding(ENCODING_NAME)
    return len(enc.encode(text))


# ── token ledger ────────────────────────────────────────────────────────────
# The ledger has two count columns:
#   local_estimate   — tiktoken, available before the API call
#   provider_reported — input_tokens + cache_read_input_tokens
#                       + cache_creation_input_tokens from usage{}
#                       (filled in after a real run; never simulated in cassettes)

BUDGET = 8_192  # example: a small model's context window (make this per-model config, not a constant)

def print_ledger(messages: list[dict[str, str]], system: str = "") -> None:
    rows: list[tuple[str, str, int]] = []

    if system:
        rows.append(("system", system, count(system)))

    for msg in messages:
        rows.append((msg["role"], msg["content"], count(msg["content"])))

    running = 0
    col_w = 40

    header = f"{'role':<12} {'tokens':>7}  {'running':>8}  {'text':<{col_w}}"
    print(header)
    print("-" * len(header))

    for role, text, tokens in rows:
        running += tokens
        display = text[:col_w - 3] + "..." if len(text) > col_w else text
        print(f"{role:<12} {tokens:>7}  {running:>8}  {display}")

    remaining = BUDGET - running
    print("-" * len(header))
    print(f"{'TOTAL':<12} {running:>7}  {'':>8}  budget={BUDGET}, remaining={remaining}")
    print()
    print("local_estimate (tiktoken)  :", running)
    print("provider_reported          : <empty — fill from usage{} after a live run>")
    print("  = input_tokens + cache_read_input_tokens + cache_creation_input_tokens")
    print("  NOTE: cache_read_input_tokens is recorded, not simulated — TTL-dependent")


# ── demo conversation ────────────────────────────────────────────────────────

SYSTEM = "You are a helpful assistant. Always format code examples with a language tag."

MESSAGES = [
    {"role": "user",      "content": "What is a token n the context of a language model?"},
    {"role": "assistant", "content": "A token is a chunk of text that the model processes as a unit. For English text, a token is roughly 3-4 characters or about 0.75 words. The word 'unbelievably' splits into three tokens: 'un', 'believ', 'ably'."},
    {"role": "user",      "content": "Why does the context window matter for context compaction?"},
    {"role": "assistant", "content": "The context window is the hard limit on how many tokens the model can read at once. Once it's full, the harness must drop or summarize older messages. That's compaction — and whatever gets dropped is what the agent can no longer act on."},
    {"role": "user",      "content": "What happens if the system prompt is doubled in length?"},
]

if __name__ == "__main__":
    print(f"\n=== Token ledger (encoding: {ENCODING_NAME}) ===\n")
    print_ledger(MESSAGES, system=SYSTEM)

    # sanity: individual string counts
    print("\n--- individual counts ---")
    examples = [
        "A typical English sentence has around twelve to fifteen words.",
        "def add(a: int, b: int) -> int:\n    return a + b",
        "3f6a1b2c-4d5e-6f7a-8b9c-0d1e2f3a4b5c",  # UUID
    ]
    for s in examples:
        preview = repr(s)[:60]
        print(f"  {count(s):>4} tokens  |  {preview}")
