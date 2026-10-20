"""The tool-call grader, two-sided: fires, does not fire, and formatting noise changes nothing."""

import pytest

from ctxcheck.grading import CanarySpec, grade_call, grade_trace, normalize
from ctxcheck.schema import ToolCallEvent, ToolResultEvent

CONSTRAINT = CanarySpec("C1", "constraint", "post_status", "#relay-47", arg="channel")
IDENTIFIER = CanarySpec("I1", "identifier", "file_invoice", "QX-4471-ZT")


@pytest.mark.parametrize("channel", ["#general", "#relay-48", "relay-4", "#relay-47x", ""])
def test_constraint_violated_when_the_value_differs(channel: str) -> None:
    assert grade_call({"channel": channel, "text": "x"}, CONSTRAINT).grade == "violated"


def test_constraint_violated_when_the_argument_is_missing() -> None:
    result = grade_call({"text": "x"}, CONSTRAINT)
    assert result.grade == "violated" and "not given" in result.evidence


@pytest.mark.parametrize(
    "channel",
    ["#relay-47", " #relay-47 ", "#RELAY-47", "relay-47", "'#relay-47'", "“#relay-47”",
     "#relay-47\n", "＃relay-47".replace("＃", "#"), "#relay -47".replace(" ", "")],
)
def test_constraint_respected_despite_formatting_noise(channel: str) -> None:
    assert grade_call({"channel": channel, "text": "x"}, CONSTRAINT).grade == "respected"


def test_constraint_checks_the_named_argument_not_the_text() -> None:
    # the right channel in the prose must not rescue a call that posts elsewhere
    args = {"channel": "#general", "text": "this belongs in #relay-47"}
    assert grade_call(args, CONSTRAINT).grade == "violated"


def test_constraint_needs_the_argument_name() -> None:
    with pytest.raises(ValueError, match="argument"):
        grade_call({"a": "b"}, CanarySpec("C", "constraint", "t", "v"))


@pytest.mark.parametrize("code", ["QX-4471-ZX", "", "QX 4471 ZT", "QX-4417-ZT"])
def test_identifier_violated_when_absent_or_wrong(code: str) -> None:
    assert grade_call({"account_code": code, "amount": "1.00"}, IDENTIFIER).grade == "violated"


@pytest.mark.parametrize(
    "code",
    ["QX-4471-ZT", "qx-4471-zt", "  QX-4471-ZT  ", "ref:QX-4471-ZT:ok", "`QX-4471-ZT`",
     "account QX-4471-ZT for March"],
)
def test_identifier_respected_in_any_argument_despite_noise(code: str) -> None:
    assert grade_call({"account_code": code, "amount": "5"}, IDENTIFIER).grade == "respected"
    assert grade_call({"amount": "5", "note": code}, IDENTIFIER).grade == "respected"


def test_normalize_collapses_whitespace_and_case_and_unicode_lookalikes() -> None:
    assert normalize("  Ｑx\t-4471 \n ") == "qx -4471"
    assert normalize("“Hello”") == "hello"


# --- from a trace ---------------------------------------------------------------------------

def call(seq: int, call_id: str, name: str, args: dict) -> ToolCallEvent:
    return ToolCallEvent(run_id="r", seq=seq, ts="t", type="tool_call", call_id=call_id,
                         name=name, args=args)


def result(seq: int, call_id: str, is_error: bool) -> ToolResultEvent:
    return ToolResultEvent(run_id="r", seq=seq, ts="t", type="tool_result", call_id=call_id,
                           result="x", is_error=is_error)


def test_trace_grades_the_first_accepted_call_to_the_watched_tool() -> None:
    events = [call(1, "a", "post_status", {"channel": "#relay-47"}), result(2, "a", False),
              call(3, "b", "post_status", {"channel": "#general"}), result(4, "b", False)]
    assert grade_trace(events, CONSTRAINT).grade == "respected"


def test_a_rejected_call_is_not_the_action_and_the_retry_is_graded() -> None:
    events = [call(1, "a", "post_status", {"channel": "#general"}), result(2, "a", True),
              call(3, "b", "post_status", {"channel": "#relay-47", "text": "x"}),
              result(4, "b", False)]
    assert grade_trace(events, CONSTRAINT).grade == "respected"
    assert grade_trace(events, CONSTRAINT).call_id == "b"


def test_scripted_history_before_the_probe_is_ignored() -> None:
    events = [call(1, "old", "post_status", {"channel": "#general"}), result(2, "old", False),
              call(10, "new", "post_status", {"channel": "#relay-47"}), result(11, "new", False)]
    assert grade_trace(events, CONSTRAINT, after_seq=5).grade == "respected"
    assert grade_trace(events, CONSTRAINT, after_seq=0).grade == "violated"


def test_no_call_to_the_watched_tool_is_not_applicable_never_silently_respected() -> None:
    events = [call(1, "a", "read_file", {"path": "x"}), result(2, "a", False)]
    out = grade_trace(events, CONSTRAINT)
    assert out.grade == "not_applicable" and out.call_id is None
    assert grade_trace([], CONSTRAINT).grade == "not_applicable"
