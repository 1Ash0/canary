"""Budget guard (ADR-012, ADR-018): nothing live runs unless it is provably within the caps.

Zero spend is the default: `max_usd=0` means only models the price table marks free may be called,
and a model missing from the table is refused (its price cannot be shown to be free). Free tiers
run out of requests and tokens long before money, so caps on both exist per run and per day.

Prices are never hard-coded: the table is a user-supplied, dated JSON file. The guard checks
*before* every call and records what a call actually used *after* it. Put it below the cassette
layer so a replay costs nothing and counts against nothing.
"""

from __future__ import annotations

import json
import math
import os
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ctxcheck.harness.types import Message, ModelResponse, ToolSpec
from ctxcheck.providers.base import Provider
from ctxcheck.tokens import count


class BudgetError(Exception):
    """A call was refused. Nothing was sent to the provider."""


class UnknownModel(BudgetError):
    pass


class NotFree(BudgetError):
    pass


class BudgetExceeded(BudgetError):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True)
class ModelPrice:
    free: bool
    input_per_mtok: float = 0.0
    output_per_mtok: float = 0.0
    as_of: str = ""
    source: str = ""

    def cost(self, input_tokens: int, output_tokens: int) -> float:
        if self.free:
            return 0.0
        return (input_tokens * self.input_per_mtok + output_tokens * self.output_per_mtok) / 1e6


@dataclass
class PriceTable:
    prices: dict[tuple[str, str], ModelPrice] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path) -> PriceTable:
        rows = json.loads(path.read_text(encoding="utf-8"))
        table = cls()
        for r in rows:
            for need in ("provider", "model", "free", "as_of", "source"):
                if need not in r:
                    raise ValueError(f"price row {r!r} is missing {need!r} (rows must be dated)")
            table.prices[(r["provider"], r["model"])] = ModelPrice(
                free=bool(r["free"]), input_per_mtok=float(r.get("input_per_mtok", 0)),
                output_per_mtok=float(r.get("output_per_mtok", 0)), as_of=r["as_of"],
                source=r["source"],
            )
        return table

    def lookup(self, provider: str, model: str) -> ModelPrice | None:
        return self.prices.get((provider, model))


@dataclass(frozen=True)
class Budget:
    max_usd: float = 0.0
    max_requests: int = 0  # per run; 0 means nothing may run until a cap is chosen on purpose
    max_tokens: int = 0  # per run, input + output
    daily_requests: int | None = None
    daily_tokens: int | None = None


class UsageStore:
    """Per-provider daily counters in a small JSON file, so day caps survive across runs."""

    def __init__(self, path: Path, today: Callable[[], str] | None = None) -> None:
        self.path = path
        self._today = today or (lambda: datetime.now(UTC).date().isoformat())

    def _read(self) -> dict[str, Any]:
        return json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else {}

    def today(self, provider: str) -> dict[str, int]:
        day = self._read().get(self._today(), {})
        entry = day.get(provider, {})
        return {"requests": entry.get("requests", 0), "tokens": entry.get("tokens", 0)}

    def add(self, provider: str, requests: int, tokens: int) -> None:
        data = self._read()
        day = data.setdefault(self._today(), {})
        entry = day.setdefault(provider, {"requests": 0, "tokens": 0})
        entry["requests"] += requests
        entry["tokens"] += tokens
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(tmp, self.path)


def estimate_input_tokens(
    messages: Sequence[Message], tools: Sequence[ToolSpec], count_fn: Callable[[str], int] = count
) -> int:
    tool_text = json.dumps([{"n": t.name, "d": t.description, "s": t.input_schema} for t in tools])
    return sum(m.tokens_est for m in messages) + (count_fn(tool_text) if tools else 0)


class GuardedProvider:
    def __init__(
        self,
        inner: Provider,
        *,
        provider_name: str,
        model: str,
        prices: PriceTable,
        budget: Budget,
        usage: UsageStore,
        count_fn: Callable[[str], int] = count,
        default_max_output: int = 1024,
    ) -> None:
        self._inner = inner
        self.provider_name = provider_name
        self.model = model
        self._prices = prices
        self._budget = budget
        self._usage = usage
        self._count = count_fn
        self._default_out = default_max_output
        self.requests = 0
        self.tokens = 0
        self.usd = 0.0

    def __repr__(self) -> str:
        return f"GuardedProvider({self.provider_name}/{self.model})"

    def _check(self, est_tokens: int) -> ModelPrice:
        price = self._prices.lookup(self.provider_name, self.model)
        if price is None:
            raise UnknownModel(
                f"{self.provider_name}/{self.model} is not in the price table, so it cannot be "
                "shown to be free. Add a dated row, or choose a listed model."
            )
        b = self._budget
        if not price.free and b.max_usd <= 0:
            raise NotFree(f"{self.model} is not free and the budget is $0 (ADR-018)")
        if self.requests + 1 > b.max_requests:
            raise BudgetExceeded(f"run request cap {b.max_requests} reached")
        if self.tokens + est_tokens > b.max_tokens:
            raise BudgetExceeded(f"run token cap {b.max_tokens} would be exceeded")
        if not price.free and self.usd >= b.max_usd:
            raise BudgetExceeded(f"usd cap {b.max_usd} reached")
        today = self._usage.today(self.provider_name)
        if b.daily_requests is not None and today["requests"] + 1 > b.daily_requests:
            raise BudgetExceeded(f"daily request cap {b.daily_requests} reached")
        if b.daily_tokens is not None and today["tokens"] + est_tokens > b.daily_tokens:
            raise BudgetExceeded(f"daily token cap {b.daily_tokens} would be exceeded")
        return price

    def complete(
        self,
        messages: Sequence[Message],
        tools: Sequence[ToolSpec],
        params: dict[str, Any],
        trial_index: int,
    ) -> ModelResponse:
        est_in = estimate_input_tokens(messages, tools, self._count)
        est_out = int(params.get("max_tokens", self._default_out))
        price = self._check(est_in + est_out)  # raises before anything is sent
        response = self._inner.complete(messages, tools, params, trial_index)
        used_in = response.input_tokens or est_in
        used_out = response.output_tokens or self._count(response.text)
        self.requests += 1
        self.tokens += used_in + used_out
        self.usd += price.cost(used_in, used_out)
        self._usage.add(self.provider_name, 1, used_in + used_out)
        return response


@dataclass(frozen=True)
class Plan:
    trials: int
    calls: int
    input_tokens: int
    output_tokens: int
    usd: float
    free: bool
    fits_run_caps: bool
    days_needed: int | None  # None when no daily cap is set
    warnings: tuple[str, ...]


def plan(
    *,
    trials: int,
    calls_per_trial: int,
    input_tokens_per_call: int,
    output_tokens_per_call: int,
    price: ModelPrice | None,
    budget: Budget,
) -> Plan:
    """A dry-run estimate. Nothing is sent. Upper-bound style: it assumes every call is made."""
    calls = trials * calls_per_trial
    tin, tout = calls * input_tokens_per_call, calls * output_tokens_per_call
    warnings: list[str] = []
    free = price is not None and price.free
    usd = 0.0 if price is None else price.cost(tin, tout)
    if price is None:
        warnings.append("model not in the price table: it would be refused")
    elif not price.free and budget.max_usd <= 0:
        warnings.append("model is not free and the budget is $0: it would be refused")
    if usd > budget.max_usd:
        warnings.append(f"estimated ${usd:.4f} exceeds the ${budget.max_usd:.2f} cap")
    fits = calls <= budget.max_requests and tin + tout <= budget.max_tokens
    if not fits:
        warnings.append("exceeds the per-run request or token cap")
    days = None
    if budget.daily_requests or budget.daily_tokens:
        by_req = math.ceil(calls / budget.daily_requests) if budget.daily_requests else 1
        by_tok = math.ceil((tin + tout) / budget.daily_tokens) if budget.daily_tokens else 1
        days = max(by_req, by_tok)
    return Plan(trials, calls, tin, tout, usd, free, fits, days, tuple(warnings))
