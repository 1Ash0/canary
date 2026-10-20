"""CLI: plan and add-price send nothing; smoke refuses unlisted models before any request."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from ctxcheck import cli
from ctxcheck.harness.types import ModelResponse, ToolCall
from ctxcheck.providers.scripted import ScriptedProvider
from ctxcheck.providers.simulated import SimulatedAgent

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


def run_args(tmp_path: Path, *extra: str) -> list[str]:
    return ["run", "--exp", "EXP-T", "--seeds", "2", "--results", str(tmp_path / "res"),
            "--runs", str(tmp_path / "runs"), "--cassettes", str(tmp_path / "cass"), *extra]


def test_simulated_dry_run_sends_nothing_and_writes_nothing(tmp_path) -> None:
    r = runner.invoke(cli.app, run_args(tmp_path, "--simulated", "--dry-run"))
    assert r.exit_code == 0 and "SIMULATED" in r.output and "nothing is sent" in r.output
    assert not (tmp_path / "res").exists()


def test_simulated_run_then_report_is_labelled_simulated_everywhere(tmp_path) -> None:
    r = runner.invoke(cli.app, run_args(tmp_path, "--simulated"))
    assert r.exit_code == 0 and "ran 8" in r.output
    out_dir = tmp_path / "res" / "simulated" / "EXP-T"  # never beside real results
    assert (out_dir / "episodes.jsonl").exists()
    rep = runner.invoke(cli.app, ["report", str(out_dir)])
    assert rep.exit_code == 0 and "SIMULATED (not measured)" in rep.output
    summary = json.loads((out_dir / "summary.json").read_text(encoding="utf-8"))
    assert summary["source"] == "simulated" and summary["n_episodes"] == 8


def test_a_second_run_resumes_and_does_nothing(tmp_path) -> None:
    runner.invoke(cli.app, run_args(tmp_path, "--simulated"))
    again = runner.invoke(cli.app, run_args(tmp_path, "--simulated"))
    assert "ran 0, skipped 8" in again.output


def test_live_run_needs_a_preset_and_model(tmp_path) -> None:
    r = runner.invoke(cli.app, run_args(tmp_path))
    assert r.exit_code != 0 and "--simulated" in r.output


def test_live_dry_run_flags_an_unlisted_model(tmp_path, files) -> None:
    r = runner.invoke(cli.app, run_args(tmp_path, "--preset", "openrouter", "--model", "unlisted",
                                        "--prices", files["prices"], "--dry-run",
                                        "--max-requests", "100", "--max-tokens", "10000000"))
    assert r.exit_code == 1 and "would be refused" in r.output


def test_live_run_without_the_key_stops_before_anything(tmp_path, files, monkeypatch) -> None:
    add_free(files)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    r = runner.invoke(cli.app, run_args(tmp_path, "--preset", "openrouter", "--model", "m:free",
                                        "--prices", files["prices"], "--usage", files["usage"]))
    assert r.exit_code == 2 and "OPENROUTER_API_KEY" in r.output


def test_live_run_records_cassettes_under_the_guard_then_replays_for_free(
    tmp_path, files, monkeypatch
) -> None:
    add_free(files)
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test-not-real")
    inner = SimulatedAgent(seed=1)
    monkeypatch.setattr(cli, "_build_provider", lambda preset, model: inner)
    common = ["--preset", "openrouter", "--model", "m:free", "--prices", files["prices"],
              "--usage", files["usage"], "--max-requests", "50", "--max-tokens", "1000000"]
    first = runner.invoke(cli.app, run_args(tmp_path, *common))
    assert first.exit_code == 0, first.output
    episodes = tmp_path / "res" / "EXP-T" / "episodes.jsonl"
    rows = [json.loads(line) for line in episodes.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 8 and {r["source"] for r in rows} == {"recorded"}
    used = json.loads(Path(files["usage"]).read_text(encoding="utf-8"))
    assert sum(d["openrouter"]["requests"] for d in used.values()) == 10  # 2 seeds x (4 + 1)

    (tmp_path / "res" / "EXP-T" / "episodes.jsonl").unlink()  # forget results, keep cassettes
    monkeypatch.delenv("OPENROUTER_API_KEY")
    replay = runner.invoke(cli.app, run_args(tmp_path, *common, "--mode", "replay"))
    assert replay.exit_code == 0 and "ran 8" in replay.output
    assert "missing cassettes 0" in replay.output
    used_after = json.loads(Path(files["usage"]).read_text(encoding="utf-8"))
    assert used_after == used  # a replay spends no quota


def test_a_request_cap_stops_cleanly_and_a_rerun_resumes(tmp_path, files, monkeypatch) -> None:
    add_free(files)
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test-not-real")
    monkeypatch.setattr(cli, "_build_provider", lambda preset, model: SimulatedAgent(seed=1))
    base = ["--preset", "openrouter", "--model", "m:free", "--prices", files["prices"],
            "--usage", files["usage"], "--max-tokens", "1000000"]
    stopped = runner.invoke(cli.app, run_args(tmp_path, *base, "--max-requests", "4"))
    assert stopped.exit_code == 3 and "stopped early" in stopped.output
    resumed = runner.invoke(cli.app, run_args(tmp_path, *base, "--max-requests", "50"))
    assert resumed.exit_code == 0 and "skipped" in resumed.output
    episodes = tmp_path / "res" / "EXP-T" / "episodes.jsonl"
    assert len(episodes.read_text(encoding="utf-8").splitlines()) == 8  # cassettes: free resume


def test_survival_command_writes_a_labelled_grid_without_any_key(tmp_path) -> None:
    out = tmp_path / "grid.json"
    r = runner.invoke(cli.app, ["survival", "--seeds", "2", "--out", str(out)])
    assert r.exit_code == 0 and "no model" in r.output
    grid = json.loads(out.read_text(encoding="utf-8"))
    assert grid["epistemic"] == "deterministic" and grid["seeds_per_cell"] == 2
