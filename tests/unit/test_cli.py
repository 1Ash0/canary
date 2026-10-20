"""CLI: plan and add-price send nothing; smoke refuses unlisted models before any request."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from ctxcheck import cli
from ctxcheck.harness.types import ModelResponse, ToolCall
from ctxcheck.providers.scripted import ScriptedProvider

runner = CliRunner()


@pytest.fixture
def files(tmp_path: Path) -> dict[str, str]:
    return {"prices": str(tmp_path / "prices.json"), "usage": str(tmp_path / "usage.json")}


def add_free(files: dict[str, str], model: str = "m:free") -> None:
    r = runner.invoke(cli.app, ["add-price", "--preset", "openrouter", "--model", model, "--free",
                                "--source", "https://x", "--prices", files["prices"]])
    assert r.exit_code == 0, r.output


def test_add_price_writes_a_dated_row_and_replaces_the_same_model(files) -> None:
    add_free(files)
    add_free(files)
    rows = json.loads(Path(files["prices"]).read_text(encoding="utf-8"))
    assert len(rows) == 1 and rows[0]["free"] is True and rows[0]["as_of"]


def test_plan_passes_for_a_listed_free_model_within_caps(files) -> None:
    add_free(files)
    r = runner.invoke(cli.app, ["plan", "--preset", "openrouter", "--model", "m:free",
                                "--trials", "2", "--calls-per-trial", "3", "--max-requests", "10",
                                "--max-tokens", "100000", "--prices", files["prices"]])
    assert r.exit_code == 0 and "nothing is sent" in r.output and "free=True" in r.output


def test_plan_fails_for_an_unlisted_model(files) -> None:
    r = runner.invoke(cli.app, ["plan", "--preset", "openrouter", "--model", "unknown",
                                "--trials", "1", "--max-requests", "10", "--max-tokens", "10000",
                                "--prices", files["prices"]])
    assert r.exit_code == 1 and "would be refused" in r.output


def test_smoke_without_the_key_set_stops_and_names_the_variable(files, monkeypatch) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    r = runner.invoke(cli.app, ["smoke", "--preset", "openrouter", "--model", "m:free",
                                "--prices", files["prices"], "--usage", files["usage"]])
    assert r.exit_code == 2 and "OPENROUTER_API_KEY" in r.output


def test_smoke_refuses_an_unlisted_model_before_sending(files, monkeypatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test-not-real")
    inner = ScriptedProvider([])
    monkeypatch.setattr(cli, "_build_provider", lambda preset, model: inner)
    r = runner.invoke(cli.app, ["smoke", "--preset", "openrouter", "--model", "unlisted",
                                "--prices", files["prices"], "--usage", files["usage"]])
    assert r.exit_code == 3 and "refused before sending" in r.output and inner.requests == []
    assert "sk-test-not-real" not in r.output


def test_smoke_passes_when_the_model_makes_the_tool_call(files, monkeypatch) -> None:
    add_free(files)
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test-not-real")
    reply = ModelResponse(tool_call=ToolCall("c1", "report", {"word": "pong"}), input_tokens=20,
                          output_tokens=5)
    monkeypatch.setattr(cli, "_build_provider", lambda preset, model: ScriptedProvider([reply]))
    r = runner.invoke(cli.app, ["smoke", "--preset", "openrouter", "--model", "m:free",
                                "--prices", files["prices"], "--usage", files["usage"]])
    assert r.exit_code == 0 and "PASS" in r.output and "requests used: 1" in r.output


def test_smoke_fails_clearly_when_the_model_does_not_call_the_tool(files, monkeypatch) -> None:
    add_free(files)
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test-not-real")
    monkeypatch.setattr(cli, "_build_provider",
                        lambda p, m: ScriptedProvider([ModelResponse(text="pong"),
                                                       ModelResponse(text="pong")]))
    r = runner.invoke(cli.app, ["smoke", "--preset", "openrouter", "--model", "m:free",
                                "--prices", files["prices"], "--usage", files["usage"]])
    assert r.exit_code == 1 and "FAIL" in r.output and "tool calling" in r.output


def test_run_dry_run_sends_nothing() -> None:
    r = runner.invoke(cli.app, ["run", "--scenario", "s", "--policy", "p", "--dry-run"])
    assert r.exit_code == 0 and "no API calls" in r.output
