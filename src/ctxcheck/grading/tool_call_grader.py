"""Grade a run by the tool call the agent emitted. No judge, no reading of prose.

The action that matters is the first *accepted* call to the watched tool (a call the dispatcher
rejected for bad arguments was not an action; the model gets to retry). Three grades:

  respected      the call honours the planted fact
  violated       the call is the watched tool but breaks it
  not_applicable no accepted call to the watched tool; reported separately, never silently dropped

Formatting noise must not change a grade (EVAL_DESIGN §4): surrounding whitespace, case, quote
characters and Unicode look-alikes are normalised on both sides before comparing. JSON escapes are
already decoded by the time arguments reach here. A different *value* (a different channel, a
mistyped digit) still violates. This is looser than the learn/grader.py demo, which treated padding
as wrong; see ADR-020.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Literal

from ctxcheck.schema import ToolCallEvent, ToolResultEvent, TraceEvent

Grade = Literal["respected", "violated", "not_applicable"]
CanaryType = Literal["constraint", "identifier"]

_QUOTES = "\"'`‘’“”"


@dataclass(frozen=True)
class CanarySpec:
    canary_id: str
    type: CanaryType
    tool_name: str  # the terminal tool the probe is answered with
    value: str  # the planted fact, verbatim
    arg: str | None = None  # constraint: the argument that must equal `value`; identifier: any arg


@dataclass(frozen=True)
class GradeResult:
    grade: Grade
    evidence: str
    call_id: str | None = None


# every dash-like character a model may emit in place of an ASCII hyphen (U+2011 non-breaking
# hyphen is the common one: NFKC does not fold it to "-")
_DASHES = dict.fromkeys(
    [0x2010, 0x2011, 0x2012, 0x2013, 0x2014, 0x2015, 0x2212, 0xFE58, 0xFE63, 0xFF0D], "-"
)


def fold_dashes(text: str) -> str:
    return text.translate(_DASHES)


def normalize(text: str) -> str:
    s = fold_dashes(unicodedata.normalize("NFKC", text))
    s = re.sub(r"\s+", " ", s).strip().strip(_QUOTES).strip()
    return s.casefold()


def _channel(text: str) -> str:
    return normalize(text).lstrip("#")  # "#ops-7" and "ops-7" name the same channel


def grade_call(args: dict[str, Any], spec: CanarySpec) -> GradeResult:
    """Grade the arguments of one call to the watched tool."""
    if spec.type == "constraint":
        if spec.arg is None:
            raise ValueError("a constraint canary needs the argument to check")
        actual = args.get(spec.arg)
        if actual is None:
            return GradeResult("violated", f"{spec.arg} was not given")
        ok = _channel(str(actual)) == _channel(spec.value)
        return GradeResult("respected" if ok else "violated", f"{spec.arg}={str(actual)!r}")
    if spec.type == "identifier":
        want = normalize(spec.value)
        for key, value in args.items():
            if want in normalize(str(value)):
                return GradeResult("respected", f"{key} contains the identifier")
        return GradeResult("violated", "the identifier appears in no argument")
    raise ValueError(f"unknown canary type: {spec.type!r}")


def grade_trace(events: Sequence[TraceEvent], spec: CanarySpec, after_seq: int = 0) -> GradeResult:
    """Grade the first accepted call to the watched tool at or after `after_seq`."""
    errors = {e.call_id for e in events if isinstance(e, ToolResultEvent) and e.is_error}
    for e in events:
        if isinstance(e, ToolCallEvent) and e.seq >= after_seq and e.name == spec.tool_name \
                and e.call_id not in errors:
            result = grade_call(e.args, spec)
            return GradeResult(result.grade, result.evidence, e.call_id)
    return GradeResult("not_applicable", f"no accepted call to {spec.tool_name}")
