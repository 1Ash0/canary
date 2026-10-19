"""
learn/policy_recency.py — U4 recency-truncate compaction policy

Run:  uv run python learn/policy_recency.py

What this shows:
  1. recency_truncate: drop oldest messages first until under budget
  2. The tool-pairing invariant: a tool_call and its tool_result are always
     dropped together — dropping one without the other crashes the next API call
  3. The system prompt is never dropped — it's the one message the agent
     always needs
  4. Idempotency: applying the policy when already under budget is a no-op

Message roles used here (flat list, one dict per message):
  system      — the standing instructions (never dropped)
  user        — human turn
  assistant   — model reply
  tool_call   — model asks to call a tool  ┐ must be kept/dropped together
  tool_result — the tool's response        ┘

The real policy lives in src/ctxcheck/policies/ (built in M3).
"""

from __future__ import annotations

import tiktoken

_enc = tiktoken.get_encoding("cl100k_base")

def token_count(text: str) -> int:
    return len(_enc.encode(text))


# ── droppable units ──────────────────────────────────────────────────────────
# A "unit" is the smallest thing we can safely remove.
# For regular messages: one message = one unit.
# For tool interactions: tool_call + tool_result = one unit (inseparable).
# The system prompt is never a unit — it is never dropped.

def _build_units(messages: list[dict]) -> list[list[int]]:
    """
    Return a list of droppable units, each a list of message indices.
    Oldest unit first. System prompt excluded.
    """
    units: list[list[int]] = []
    start = 1 if messages and messages[0]["role"] == "system" else 0
    i = start
    while i < len(messages):
        if messages[i]["role"] == "tool_call":
            # The very next message must be its tool_result.
            # Drop them together or not at all.
            if i + 1 < len(messages) and messages[i + 1]["role"] == "tool_result":
                units.append([i, i + 1])
                i += 2
            else:
                # Malformed trace: orphaned tool_call. Treat as single unit.
                units.append([i])
                i += 1
        elif messages[i]["role"] == "tool_result":
            # Orphaned tool_result (its tool_call was already dropped somehow).
            # Treat as single unit so we can still make progress.
            units.append([i])
            i += 1
        else:
            units.append([i])
            i += 1
    return units


def _total_tokens(messages: list[dict]) -> int:
    return sum(m["tokens"] for m in messages)


# ── policy ───────────────────────────────────────────────────────────────────

def recency_truncate(messages: list[dict], budget: int) -> list[dict]:
    """
    Drop the oldest droppable unit repeatedly until total tokens <= budget.
    Returns a new list; the original is unchanged.

    Invariants:
    - System prompt is never dropped.
    - tool_call and tool_result are always dropped together.
    - If already under budget, returns the original list unchanged (idempotency).
    """
    if _total_tokens(messages) <= budget:
        return list(messages)  # already fine — copy, don't mutate

    result = list(messages)  # work on a copy

    while _total_tokens(result) > budget:
        units = _build_units(result)
        if not units:
            # Nothing left to drop (only the system prompt remains).
            break
        # Drop the oldest unit (first in list).
        oldest = units[0]
        # Remove in reverse index order so earlier indices stay valid.
        for idx in reversed(oldest):
            result.pop(idx)

    return result


# ── demo ─────────────────────────────────────────────────────────────────────

def make_msg(role: str, content: str) -> dict:
    return {"role": role, "content": content, "tokens": token_count(content)}

def print_messages(messages: list[dict], label: str) -> None:
    total = _total_tokens(messages)
    print(f"\n── {label} ({total} tokens) ──────────────────────────────")
    for i, m in enumerate(messages):
        preview = m["content"][:55].replace("\n", " ")
        print(f"  [{i}] {m['role']:<12}  {m['tokens']:>4}t  {preview}")

if __name__ == "__main__":
    # A conversation with: system prompt, canary turn (the rule),
    # several filler turns, a tool interaction, and a final probe.
    messages = [
        make_msg("system",      "You are a helpful assistant."),
        make_msg("user",        "IMPORTANT: always send status updates to channel #ops-7."),  # canary
        make_msg("assistant",   "Understood. I will use #ops-7 for all status updates."),
        make_msg("user",        "Write a Python function that reverses a list."),             # filler
        make_msg("assistant",   "def reverse(lst): return lst[::-1]"),
        make_msg("user",        "What is the capital of France?"),                            # filler
        make_msg("assistant",   "Paris."),
        make_msg("tool_call",   '{"name": "read_file", "args": {"path": "report.txt"}}'),    # tool pair
        make_msg("tool_result", "File contents: Q3 revenue up 12%."),                        # must stay with tool_call
        make_msg("user",        "Send the weekly status update now."),                        # probe
    ]

    BUDGET = 80  # tight budget to force compaction

    print_messages(messages, "original")
    print(f"\n  budget = {BUDGET} tokens")

    result = recency_truncate(messages, BUDGET)
    print_messages(result, f"after recency_truncate (budget={BUDGET})")

    # Which messages were dropped?
    original_indices = {id(m) for m in messages}
    kept_indices = {id(m) for m in result}
    dropped = [m for m in messages if id(m) not in kept_indices]
    print(f"\n  dropped {len(dropped)} message(s):")
    for m in dropped:
        print(f"    {m['role']:<12}  {m['content'][:60]!r}")

    # ── property: idempotency ────────────────────────────────────────────────
    print("\n── property: idempotency ───────────────────────────────────")
    already_small = messages[:3]   # only 3 messages, well under budget
    result2 = recency_truncate(already_small, budget=10_000)
    print(f"  input size:  {len(already_small)} messages")
    print(f"  output size: {len(result2)} messages")
    print(f"  same list?   {result2 == already_small}  (must be True)")

    # ── property: tool-pairing invariant ─────────────────────────────────────
    print("\n── property: tool-pairing invariant ────────────────────────")
    # Find tool_call and tool_result in result — either both present or both absent.
    roles_in_result = [m["role"] for m in result]
    has_tool_call   = "tool_call"   in roles_in_result
    has_tool_result = "tool_result" in roles_in_result
    paired = has_tool_call == has_tool_result
    print(f"  tool_call in result:   {has_tool_call}")
    print(f"  tool_result in result: {has_tool_result}")
    print(f"  invariant holds?       {paired}  (must be True)")

    # ── canary survival ───────────────────────────────────────────────────────
    print("\n── canary survival ─────────────────────────────────────────")
    canary_text = "#ops-7"
    survived = any(canary_text in m["content"] for m in result)
    print(f"  canary (#ops-7) survived compaction: {survived}")
    if not survived:
        print("  → this trial would be graded VIOLATED")
    else:
        print("  → canary intact; probe can still be graded")
