"""ctxcheck CLI.

Live calls go through the budget guard (ADR-012, ADR-018): free models only, request and token
caps. `plan` and `run --dry-run` send nothing. Keys are read from environment variables, never from
arguments or files, so they cannot end up in shell history or a commit.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path

import typer

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
from ctxcheck.providers.base import Provider
from ctxcheck.providers.presets import PRESETS, from_preset

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


@app.command()
def run(
    scenario: str = typer.Option(..., help="Scenario / canary pack name"),
    policy: str = typer.Option(..., help="Compaction policy name"),
    model: str = typer.Option("unset", help="Model to test"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print plan without running"),
) -> None:
    """Run a canary scenario under a compaction policy (wired in M4)."""
    typer.echo(f"scenario={scenario!r} policy={policy!r} model={model!r}")
    if dry_run:
        typer.echo("[dry-run] no API calls will be made. Use `ctxcheck plan` for the estimate.")
        return
    typer.echo("`run` is wired in M4 (canary packs and the experiment runner).")
    raise typer.Exit(1)


if __name__ == "__main__":
    app()
