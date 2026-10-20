"""ctxcheck CLI.

Live calls go through the budget guard (ADR-012, ADR-018): free models only, request and token
caps. `plan` and `run --dry-run` send nothing. Keys are read from environment variables, never from
arguments or files, so they cannot end up in shell history or a commit.
"""

from __future__ import annotations

import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import typer

from ctxcheck.canaries import PACKS
from ctxcheck.harness.budget import (
    Budget,
    BudgetError,
    GuardedProvider,
    PriceTable,
    UsageStore,
)
from ctxcheck.harness.budget import (
    plan as make_plan,
)
from ctxcheck.harness.loop import Scenario, Turn
from ctxcheck.harness.loop import run as run_loop
from ctxcheck.harness.tools import Tool
from ctxcheck.harness.types import ToolSpec
from ctxcheck.policies import REGISTRY
from ctxcheck.providers.base import Provider
from ctxcheck.providers.cassette import CassetteProvider
from ctxcheck.providers.presets import PRESETS, from_preset
from ctxcheck.providers.simulated import MODEL_ID, SimulatedAgent
from ctxcheck.runner.analysis import analyse
from ctxcheck.runner.experiment import ExperimentPlan, estimate_tokens, read_rows, run_experiment
from ctxcheck.runner.regrade import regrade_rows, write_rows
from ctxcheck.runner.survival import survival_grid

app = typer.Typer(
    name="ctxcheck",
    help="Test kit and flight recorder for agent context-compaction policies.",
    no_args_is_help=True,
)

DEFAULT_PRICES = Path("config/prices.json")
DEFAULT_USAGE = Path("runs/.usage.json")


def _build_provider(preset: str, model: str) -> Provider:
    """Seam for tests: they replace this so no network is ever touched."""
    return from_preset(preset, model)


def _load_prices(path: Path) -> PriceTable:
    return PriceTable.load(path) if path.exists() else PriceTable()


@app.command()
def plan(
    preset: str = typer.Option(..., help=f"Provider preset: {', '.join(sorted(PRESETS))}"),
    model: str = typer.Option(..., help="Model id, as the provider lists it"),
    trials: int = typer.Option(..., min=1),
    calls_per_trial: int = typer.Option(10, min=1, help="Upper bound of model calls per trial"),
    input_tokens: int = typer.Option(4000, min=0, help="Average input tokens per call"),
    output_tokens: int = typer.Option(300, min=0, help="Average output tokens per call"),
    max_requests: int = typer.Option(0, help="Per-run request cap"),
    max_tokens: int = typer.Option(0, help="Per-run token cap (input + output)"),
    daily_requests: int | None = typer.Option(None, help="Provider's daily request limit"),
    daily_tokens: int | None = typer.Option(None, help="Provider's daily token limit"),
    max_usd: float = typer.Option(0.0, help="Spend cap. Zero means free models only (ADR-018)"),
    prices: Path = typer.Option(DEFAULT_PRICES, help="Dated price table"),
) -> None:
    """Estimate what a run would use and whether the guard would allow it. Sends nothing."""
    budget = Budget(max_usd, max_requests, max_tokens, daily_requests, daily_tokens)
    price = _load_prices(prices).lookup(preset, model)
    p = make_plan(trials=trials, calls_per_trial=calls_per_trial,
                  input_tokens_per_call=input_tokens, output_tokens_per_call=output_tokens,
                  price=price, budget=budget)
    typer.echo("[dry-run] nothing is sent")
    typer.echo(f"calls <= {p.calls}   tokens <= {p.input_tokens + p.output_tokens}   "
               f"usd <= {p.usd:.4f}   free={p.free}   fits run caps={p.fits_run_caps}")
    if p.days_needed is not None:
        typer.echo(f"days needed at the daily limits: {p.days_needed}")
    for w in p.warnings:
        typer.echo(f"warning: {w}")
    raise typer.Exit(0 if not p.warnings else 1)


@app.command("add-price")
def add_price(
    preset: str = typer.Option(...),
    model: str = typer.Option(...),
    free: bool = typer.Option(..., "--free/--paid", help="--free only if the page says so"),
    source: str = typer.Option(..., help="URL of the page that shows this price"),
    input_per_mtok: float = typer.Option(0.0),
    output_per_mtok: float = typer.Option(0.0),
    prices: Path = typer.Option(DEFAULT_PRICES),
) -> None:
    """Add a dated row to the price table. The guard refuses any model not listed here."""
    rows = json.loads(prices.read_text(encoding="utf-8")) if prices.exists() else []
    rows = [r for r in rows if not (r["provider"] == preset and r["model"] == model)]
    rows.append({"provider": preset, "model": model, "free": free, "source": source,
                 "as_of": datetime.now(UTC).date().isoformat(),
                 "input_per_mtok": input_per_mtok, "output_per_mtok": output_per_mtok})
    prices.parent.mkdir(parents=True, exist_ok=True)
    prices.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    typer.echo(f"recorded {preset}/{model} free={free} as of today")


def _smoke_tools() -> list[Tool]:
    spec = ToolSpec("report", "Report a word back to the harness.",
                    {"type": "object", "properties": {"word": {"type": "string"}},
                     "required": ["word"]})
    return [Tool(spec, fn=lambda word: f"reported {word}", terminal=True)]


@app.command()
def smoke(
    preset: str = typer.Option(..., help=f"Provider preset: {', '.join(sorted(PRESETS))}"),
    model: str = typer.Option(..., help="Model id. Must be a row in the price table"),
    max_requests: int = typer.Option(3, help="Request cap for this check"),
    max_tokens: int = typer.Option(4000),
    daily_requests: int | None = typer.Option(None),
    prices: Path = typer.Option(DEFAULT_PRICES),
    usage: Path = typer.Option(DEFAULT_USAGE),
) -> None:
    """One tiny tool-calling request: does this key, endpoint and model work with tools?

    Sends a fixed, harmless prompt. Costs at most `max_requests` requests on a free model.
    """
    env = ""  # name of the variable, shown on failure; the value is never printed
    try:
        env = str(PRESETS[preset]["api_key_env"])
    except KeyError:
        typer.echo(f"unknown preset {preset!r}; known: {', '.join(sorted(PRESETS))}")
        raise typer.Exit(2) from None
    if not os.environ.get(env):
        typer.echo(f"{env} is not set in this shell. Set it there (not in chat) and retry.")
        raise typer.Exit(2)

    budget = Budget(0.0, max_requests, max_tokens, daily_requests)
    guarded = GuardedProvider(_build_provider(preset, model), provider_name=preset, model=model,
                              prices=_load_prices(prices), budget=budget, usage=UsageStore(usage))
    scenario = Scenario("smoke", "You are a test harness assistant. Always use the tools.",
                        [Turn("Call the report tool with the word pong.")])
    try:
        trace = run_loop(scenario, guarded, _smoke_tools(), limit_tokens=3000,
                         max_calls_per_turn=2, provider_name=preset, model=model)
    except BudgetError as e:
        typer.echo(f"refused before sending: {e}")
        raise typer.Exit(3) from None
    except Exception as e:  # provider/network errors are already scrubbed of secrets
        typer.echo(f"call failed: {type(e).__name__}: {e}")
        raise typer.Exit(4) from None

    calls = [e for e in trace if e.type == "tool_call"]
    end = trace[-1]
    typer.echo(f"requests used: {guarded.requests}   tokens: {guarded.tokens}")
    if calls and calls[0].type == "tool_call":
        typer.echo(f"PASS: the model made a tool call: {calls[0].name} {calls[0].args}")
        raise typer.Exit(0)
    typer.echo(f"FAIL: no tool call (run ended: {getattr(end, 'reason', None)}). "
               "This model may not support tool calling; pick another.")
    raise typer.Exit(1)


def _slug(text: str) -> str:
    """A directory-safe name: model ids contain ':' and '/', which Windows paths reject."""
    return re.sub(r"[^\w.-]", "_", text)


def _parse_options(opts: list[str]) -> tuple[tuple[str, Any], ...]:
    out: list[tuple[str, Any]] = []
    for item in opts:
        key, _, raw = item.partition("=")
        if not key or not raw:
            raise typer.BadParameter(f"--opt expects name=value, got {item!r}")
        value: Any = raw
        for cast in (int, float):
            try:
                value = cast(raw)
                break
            except ValueError:
                continue
        out.append((key, value))
    return tuple(out)


@app.command()
def run(
    exp: str = typer.Option(..., help="Experiment id, e.g. EXP-001 (preregister it first)"),
    pack: str = typer.Option("constraint", help=f"Canary pack: {', '.join(sorted(PACKS))}"),
    policy: str = typer.Option("llm_summary", help=f"One of: {', '.join(sorted(REGISTRY))}"),
    opt: list[str] = typer.Option([], "--opt", help="Policy option name=value (repeatable)"),
    seeds: int = typer.Option(10, min=1, help="Seeds 1..N"),
    trials: int = typer.Option(1, min=1),
    limit_tokens: int = typer.Option(2400, help="Window budget the treatment compacts against"),
    simulated: bool = typer.Option(False, "--simulated", help="Toy agent: free, NOT measured"),
    preset: str = typer.Option("", help=f"Provider preset: {', '.join(sorted(PRESETS))}"),
    model: str = typer.Option("", help="Model id; must be a row in the price table"),
    mode: str = typer.Option("auto", help="Cassette mode: auto (record misses), replay, record"),
    cassettes: Path = typer.Option(Path("cassettes"), help="Cassette root directory"),
    results: Path = typer.Option(Path("results"), help="Results root directory"),
    runs: Path = typer.Option(Path("runs"), help="Trace root directory"),
    max_requests: int = typer.Option(0, help="Per-run request cap"),
    max_tokens: int = typer.Option(0, help="Per-run token cap (input + output)"),
    daily_requests: int | None = typer.Option(None),
    daily_tokens: int | None = typer.Option(None),
    prices: Path = typer.Option(DEFAULT_PRICES),
    usage: Path = typer.Option(DEFAULT_USAGE),
    dry_run: bool = typer.Option(False, "--dry-run", help="Estimate only; send nothing"),
) -> None:
    """Run an experiment: four conditions per seed, resumable, graded by tool call."""
    if mode not in ("auto", "replay", "record"):
        raise typer.BadParameter("mode must be auto, replay or record")
    if not simulated and not (preset and model):
        raise typer.BadParameter("give --preset and --model, or --simulated")
    plan_ = ExperimentPlan(exp, pack, policy, tuple(range(1, seeds + 1)), trials,
                           policy_options=_parse_options(opt), limit_tokens=limit_tokens)
    name, model_id = ("simulated", MODEL_ID) if simulated else (preset, model)
    tin, tout = estimate_tokens(plan_)
    calls = plan_.calls_upper_bound()
    typer.echo(f"{exp}: {pack} x {policy}, {seeds} seeds x {trials} trial(s) -> "
               f"<= {calls} model calls, ~{tin + tout} tokens"
               + ("   [SIMULATED: not measured]" if simulated else ""))
    if dry_run:
        if not simulated:
            budget = Budget(0.0, max_requests, max_tokens, daily_requests, daily_tokens)
            p = make_plan(trials=1, calls_per_trial=calls, input_tokens_per_call=tin // calls,
                          output_tokens_per_call=tout // calls,
                          price=_load_prices(prices).lookup(preset, model), budget=budget)
            typer.echo(f"free={p.free}  fits run caps={p.fits_run_caps}  "
                       f"days needed at the daily limits: {p.days_needed}")
            for w in p.warnings:
                typer.echo(f"warning: {w}")
            raise typer.Exit(0 if not p.warnings else 1)
        typer.echo("[dry-run] nothing is sent")
        raise typer.Exit(0)

    provider: Provider
    if simulated:
        provider = SimulatedAgent()
        out_dir, runs_dir = results / "simulated" / exp, runs / "simulated" / exp
    else:
        if mode != "replay":
            env = str(PRESETS[preset]["api_key_env"]) if preset in PRESETS else ""
            if not env or not os.environ.get(env):
                typer.echo(f"{env or preset} is not set in this shell. Set it there (not in chat).")
                raise typer.Exit(2)
        guarded = GuardedProvider(
            _build_provider(preset, model), provider_name=preset, model=model,
            prices=_load_prices(prices),
            budget=Budget(0.0, max_requests, max_tokens, daily_requests, daily_tokens),
            usage=UsageStore(usage))
        provider = CassetteProvider(cassettes / exp / f"{preset}__{_slug(model)}",
                                    mode, inner=None if mode == "replay" else guarded,
                                    provider_name=preset, model=model)
        out_dir, runs_dir = results / exp, runs / exp

    report = run_experiment(plan_, provider, provider_name=name, model=model_id, out_dir=out_dir,
                            runs_dir=runs_dir, source="simulated" if simulated else "recorded",
                            log=typer.echo)
    typer.echo(f"ran {report.ran}, skipped {report.skipped} already done, "
               f"missing cassettes {len(report.missing_cassettes)}")
    if report.stopped:
        typer.echo(f"stopped early: {report.stopped}. Rerun the same command to resume.")
        raise typer.Exit(3)


@app.command()
def report(
    exp_dir: Path = typer.Argument(..., help="results/<exp> directory with episodes.jsonl"),
) -> None:
    """Write summary.json and print rates with Wilson intervals and the paired comparisons.

    If the directory holds an analysis.json (the preregistered comparisons, written before the
    analysis), its `primary`, `exploratory` and `bh_family` are used; otherwise the defaults.
    """
    rows = read_rows(exp_dir / "episodes.jsonl")
    if not rows:
        typer.echo(f"no episodes in {exp_dir}")
        raise typer.Exit(1)
    config_path = exp_dir / "analysis.json"
    config = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
    primary = [tuple(p) for p in config["primary"]] if "primary" in config else None
    explore = config.get("exploratory")
    if isinstance(explore, list):
        explore = [tuple(p) for p in explore]
    summary = analyse(rows, primary=primary, exploratory=explore,
                      bh_family=config.get("bh_family", "all"))
    (exp_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    tag = "SIMULATED (not measured)" if summary["source"] == "simulated" else "recorded"
    typer.echo(f"{summary['exp_id']}  {tag}  models: {', '.join(summary['models_reported'])}  "
               f"dates: {', '.join(summary['dates'])}  episodes: {summary['n_episodes']}")
    group = None
    for c in summary["cells"]:
        if (c["model"], c["pack"]) != group:
            group = (c["model"], c["pack"])
            typer.echo(f"  [{c['model']}, {c['pack']} pack]")
        if "rate" in c:
            typer.echo(f"  {c['label']:<34} violated {c['k_violated']}/{c['n_graded']} = "
                       f"{c['rate']:.0%}  [{c['wilson_lo']:.0%}, {c['wilson_hi']:.0%}]"
                       f"  n/a {c['n_not_applicable']}")
    for c in summary["comparisons"]:
        if "risk_difference" in c:
            typer.echo(f"  {c['role'][:4]} {c['model']}, {c['pack']}: "
                       f"{c['first']} vs {c['second']}: RD {c['risk_difference']:+.0%} "
                       f"[{c['rd_lo']:+.0%}, {c['rd_hi']:+.0%}]  McNemar p={c['p_mcnemar']:.3g} "
                       f"q={c['q_bh']:.3g}  ({c['only_first_failed']} vs "
                       f"{c['only_second_failed']} discordant)")


@app.command()
def survival(
    pack: str = typer.Option("constraint", help=f"Canary pack: {', '.join(sorted(PACKS))}"),
    seeds: int = typer.Option(20, min=1, help="Seeded histories per cell"),
    out: Path = typer.Option(Path("results/survival/grid.json")),
) -> None:
    """Does the planted fact survive each deterministic policy? No model is called."""
    grid = survival_grid(pack=pack, seeds=seeds)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(grid, indent=2) + "\n", encoding="utf-8", newline="\n")
    typer.echo(f"wrote {out}: {len(grid['cells'])} cells x {seeds} seeds (deterministic; no model)")


@app.command()
def regrade(
    exp_dir: Path = typer.Argument(..., help="results/<exp> directory with episodes.jsonl"),
    out: Path | None = typer.Option(None, help="Write the regraded rows to this directory instead"),
    write: bool = typer.Option(False, "--write", help="Overwrite episodes.jsonl in place"),
) -> None:
    """Re-derive grade, survival and summary validity from the traces and show what changes."""
    result = regrade_rows(read_rows(exp_dir / "episodes.jsonl"))
    for model, seed, condition, key, old, new in result.changes:
        typer.echo(f"  {model} seed {seed} {condition}: {key} {old!r} -> {new!r}")
    typer.echo(f"{len(result.changes)} change(s) in {len(result.rows)} rows")
    if out is not None:
        write_rows(out / "episodes.jsonl", result.rows)
        typer.echo(f"wrote {out / 'episodes.jsonl'}")
    elif write:
        write_rows(exp_dir / "episodes.jsonl", result.rows)
        typer.echo("episodes.jsonl rewritten in place")


if __name__ == "__main__":
    app()
