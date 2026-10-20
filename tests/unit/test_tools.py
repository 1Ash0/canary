"""Dispatcher: valid calls run; every kind of bad call becomes an error result, not an exception."""

from ctxcheck.harness.tools import Tool, dispatch
from ctxcheck.harness.types import BAD_ARGS_KEY, ToolCall, ToolSpec
from ctxcheck.providers.scripted import ScriptedProvider  # noqa: F401  (import must work)

READ = Tool(
    ToolSpec(
        "read_file", "Read a file",
        {"type": "object", "properties": {"path": {"type": "string"}, "lines": {"type": "integer"}},
         "required": ["path"]},
    ),
    fn=lambda path, lines=10: f"{lines} lines of {path}",
)
POST = Tool(
    ToolSpec(
        "post_status", "Post a status",
        {"type": "object",
         "properties": {"channel": {"type": "string"}, "text": {"type": "string"}},
         "required": ["channel", "text"]},
    ),
    fn=lambda channel, text: f"posted to {channel}",
    terminal=True,
)
BOOM_SPEC = ToolSpec("boom", "Always fails", {"type": "object", "properties": {}})
BOOM = Tool(BOOM_SPEC, fn=lambda: 1 / 0)
TOOLS = [READ, POST, BOOM]


def call(name: str, /, **args: object) -> ToolCall:
    return ToolCall("c1", name, dict(args))


def test_valid_call_runs_and_returns_the_tool() -> None:
    result, tool = dispatch(TOOLS, call("read_file", path="a.py", lines=3))
    assert (result.text, result.is_error) == ("3 lines of a.py", False)
    assert tool is READ


def test_terminal_flag_comes_back_with_the_tool() -> None:
    _, tool = dispatch(TOOLS, call("post_status", channel="#ops-7", text="done"))
    assert tool is not None and tool.terminal


def test_unknown_tool_is_an_error_result_listing_what_exists() -> None:
    result, tool = dispatch(TOOLS, call("delete_branch", name="main"))
    assert result.is_error and tool is None
    assert "unknown tool" in result.text and "read_file" in result.text


def test_missing_required_argument_is_an_error_result() -> None:
    result, _ = dispatch(TOOLS, call("read_file"))
    assert result.is_error and "missing required argument 'path'" in result.text


def test_unknown_argument_is_an_error_result() -> None:
    result, _ = dispatch(TOOLS, call("read_file", path="a", colour="red"))
    assert result.is_error and "unknown argument 'colour'" in result.text


def test_wrong_argument_type_is_an_error_result() -> None:
    assert dispatch(TOOLS, call("read_file", path=5))[0].is_error
    assert dispatch(TOOLS, call("read_file", path="a", lines="3"))[0].is_error


def test_bool_is_not_accepted_as_an_integer() -> None:
    assert dispatch(TOOLS, call("read_file", path="a", lines=True))[0].is_error


def test_undecodable_arguments_are_reported_as_such_not_as_a_missing_argument() -> None:
    result, tool = dispatch(TOOLS, call("read_file", **{BAD_ARGS_KEY: '{"path": '}))
    assert result.is_error and tool is READ
    assert "not valid JSON" in result.text and "missing" not in result.text


def test_a_tool_that_raises_is_reported_not_fatal() -> None:
    result, _ = dispatch(TOOLS, call("boom"))
    assert result.is_error and "boom failed" in result.text


def test_a_correct_call_after_a_bad_one_still_works() -> None:
    assert dispatch(TOOLS, call("nope"))[0].is_error
    assert not dispatch(TOOLS, call("read_file", path="a"))[0].is_error
