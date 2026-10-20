"""Tools and the dispatcher.

A model's tool call is untrusted input: the name may not exist and the arguments may be the wrong
shape. The dispatcher never raises for either; it returns an error result, which the loop sends back
to the model like any other result, so one bad call does not end the run.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

from ctxcheck.harness.types import ToolCall, ToolSpec


@dataclass(frozen=True)
class Tool:
    spec: ToolSpec
    fn: Callable[..., str]
    terminal: bool = False  # calling it ends the run; its arguments are what the grader reads


@dataclass(frozen=True)
class ToolResult:
    text: str
    is_error: bool = False


def _check_args(spec: ToolSpec, args: dict[str, Any]) -> str | None:
    """Minimal schema check: required keys present, no unknown keys, simple types match."""
    props: dict[str, Any] = spec.input_schema.get("properties", {})
    required: list[str] = spec.input_schema.get("required", [])
    for key in required:
        if key not in args:
            return f"missing required argument {key!r}"
    for key, value in args.items():
        if key not in props:
            return f"unknown argument {key!r}"
        expected = {"string": str, "integer": int, "number": (int, float), "boolean": bool}.get(
            props[key].get("type", "")
        )
        is_bool_for_int = expected is int and isinstance(value, bool)  # True is an int in Python
        if expected and (not isinstance(value, expected) or is_bool_for_int):
            return f"argument {key!r} should be {props[key]['type']}"
    return None


def dispatch(tools: Sequence[Tool], call: ToolCall) -> tuple[ToolResult, Tool | None]:
    """Run a call. Returns the result and the matched tool (None if the name is unknown)."""
    by_name = {t.spec.name: t for t in tools}
    tool = by_name.get(call.name)
    if tool is None:
        known = ", ".join(sorted(by_name)) or "none"
        return ToolResult(f"unknown tool {call.name!r}; available: {known}", is_error=True), None
    problem = _check_args(tool.spec, call.args)
    if problem:
        return ToolResult(f"bad arguments for {call.name}: {problem}", is_error=True), tool
    try:
        return ToolResult(tool.fn(**call.args)), tool
    except Exception as exc:  # noqa: BLE001 - a failing tool is reported to the model, not fatal
        return ToolResult(f"{call.name} failed: {exc}", is_error=True), tool
