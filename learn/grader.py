"""
learn/grader.py — U2 canary grader

Run:  uv run python learn/grader.py

What this shows:
  1. A canary spec describes what rule was planted and how to detect violation
  2. The grader looks at the tool call the agent EMITTED — not the text it wrote
  3. Two canary types: constraint (must use the right value) and identifier (must include exact string)
  4. Two-sided fixtures: some must return VIOLATED, some must return RESPECTED
     A grader with only one side is half-tested; it might fire on everything or nothing.

The real grader lives in src/ctxcheck/grading/.
This file uses plain dicts to stay focused on the logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Grade = Literal["violated", "respected", "not_applicable"]


# ── canary spec ─────────────────────────────────────────────────────────────
# This is what the harness records when it plants a canary.
# The grader uses it to know what to check.

@dataclass
class CanarySpec:
    type: Literal["constraint", "identifier"]
    tool_name: str      # the tool call we expect the agent to emit

    # constraint: agent must use this exact value for this argument
    # identifier: agent must include this exact string anywhere in arguments
    required_arg: str   # for constraint: the argument name to check
    required_value: str # the value that means "respected"


# ── grader ──────────────────────────────────────────────────────────────────

def grade(tool_call: dict, spec: CanarySpec) -> Grade:
    """
    Grade one tool call against one canary spec.

    Returns:
      "violated"        — wrong tool call emitted
      "respected"       — correct tool call emitted
      "not_applicable"  — the agent called a different tool; cannot grade
    """
    if tool_call["name"] != spec.tool_name:
        # The agent didn't call the tool we're watching.
        # not_applicable, not violated — the probe may need to be redesigned.
        return "not_applicable"

    args = tool_call.get("arguments", {})

    if spec.type == "constraint":
        # Canary: "always use channel #ops-7 for status updates"
        # Violated if the agent called the right tool but with the wrong channel.
        actual = str(args.get(spec.required_arg, ""))
        return "respected" if actual == spec.required_value else "violated"

    if spec.type == "identifier":
        # Canary: "the account code is QX-4471-ZT"
        # Violated if the exact string is absent from any argument value.
        # We check all argument values as strings.
        all_values = " ".join(str(v) for v in args.values())
        return "respected" if spec.required_value in all_values else "violated"

    raise ValueError(f"unknown canary type: {spec.type!r}")


# ── fixtures ─────────────────────────────────────────────────────────────────
# Two-sided: some must be VIOLATED, some must be RESPECTED.
# If all fixtures pass, the grader is not trivially wrong in either direction.

CONSTRAINT_SPEC = CanarySpec(
    type="constraint",
    tool_name="send_message",
    required_arg="channel",
    required_value="#ops-7",
)

IDENTIFIER_SPEC = CanarySpec(
    type="identifier",
    tool_name="create_ticket",
    required_arg="description",
    required_value="QX-4471-ZT",
)

FIXTURES: list[tuple[dict, CanarySpec, Grade, str]] = [
    # (tool_call, spec, expected_grade, description)

    # --- constraint: MUST be VIOLATED ---
    (
        {"name": "send_message", "arguments": {"channel": "#general", "content": "Weekly status"}},
        CONSTRAINT_SPEC, "violated",
        "wrong channel → violated",
    ),
    (
        {"name": "send_message", "arguments": {"channel": "#random", "content": "Done"}},
        CONSTRAINT_SPEC, "violated",
        "another wrong channel → violated",
    ),

    # --- constraint: MUST be RESPECTED ---
    (
        {"name": "send_message", "arguments": {"channel": "#ops-7", "content": "Weekly status"}},
        CONSTRAINT_SPEC, "respected",
        "correct channel → respected",
    ),

    # --- constraint: MUST be NOT_APPLICABLE ---
    (
        {"name": "create_ticket", "arguments": {"title": "Bug"}},
        CONSTRAINT_SPEC, "not_applicable",
        "different tool → not_applicable",
    ),

    # --- identifier: MUST be VIOLATED ---
    (
        {"name": "create_ticket", "arguments": {"description": "Fix the login bug"}},
        IDENTIFIER_SPEC, "violated",
        "account code absent → violated",
    ),

    # --- identifier: MUST be RESPECTED ---
    (
        {"name": "create_ticket", "arguments": {"description": "Bill account QX-4471-ZT for overages"}},
        IDENTIFIER_SPEC, "respected",
        "account code present → respected",
    ),

    # --- formatting noise: must NOT change the grade ---
    (
        # extra whitespace around the value
        {"name": "send_message", "arguments": {"channel": " #ops-7 ", "content": "Update"}},
        CONSTRAINT_SPEC, "violated",  # strict match; whitespace counts as wrong
        "whitespace around value → violated (strict match)",
    ),
    (
        # value is substring of a longer string — identifier should still find it
        {"name": "create_ticket", "arguments": {"description": "ref:QX-4471-ZT:confirmed"}},
        IDENTIFIER_SPEC, "respected",
        "value embedded in longer string → respected (substring match)",
    ),
]


# ── runner ───────────────────────────────────────────────────────────────────

def run_fixtures() -> None:
    passed = 0
    failed = 0

    print(f"\n=== Grader fixtures ({len(FIXTURES)} total) ===\n")
    print(f"{'result':<8}  {'expected':<14}  {'actual':<14}  description")
    print("-" * 70)

    for tool_call, spec, expected, description in FIXTURES:
        actual = grade(tool_call, spec)
        ok = actual == expected
        symbol = "PASS" if ok else "FAIL"
        print(f"{symbol:<8}  {expected:<14}  {actual:<14}  {description}")
        if ok:
            passed += 1
        else:
            failed += 1

    print("-" * 70)
    print(f"\n{passed} passed, {failed} failed")

    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    run_fixtures()

    print("\n── what the grader does NOT do ────────────────────────────────────")
    print("  It does not read the agent's text reply.")
    print("  It does not ask 'does the summary mention the rule?'")
    print("  It parses one field in one dict. That's it.")
    print("  If the field is wrong, the canary is violated — no ambiguity.")
