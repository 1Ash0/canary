"""Budget guard: refuses before sending, never lets an unlisted or paid model through at $0."""

import json
from pathlib import Path

import pytest

from ctxcheck.harness.budget import (
    Budget,
    BudgetExceeded,
    GuardedProvider,
    ModelPrice,
    NotFree,
    PriceTable,
    UnknownModel,
    UsageStore,
    plan,
)
from ctxcheck.harness.types import Message, ModelResponse, ToolSpec

FREE = ModelPrice(free=True, as_of="2026-10-20", source="test")
PAID = ModelPrice(free=False, input_per_mtok=1.0, output_per_mtok=2.0, as_of="2026-10-20",
                  source="test")
TOOLS: list[ToolSpec] = []


def msgs(n_tokens: int = 10) -> list[Message]:
    return [Message("m1", "user", "hi", "user", n_tokens, 1)]


class Inner:
    def __init__(self, in_tok: int = 10, out_tok: int = 5) -> None:
        self.calls = 0
        self._r = ModelResponse(text="ok", input_tokens=in_tok, output_tokens=out_tok)

    def complete(self, messages, tools, params, trial_index) -> ModelResponse:
        self.calls += 1
        return self._r


def guard(tmp_path: Path, inner, price: ModelPrice | None, budget: Budget, today="2026-10-20"):
    table = PriceTable({("p", "m"): price} if price else {})
    store = UsageStore(tmp_path / "usage.json", today=lambda: today)
    return GuardedProvider(inner, provider_name="p", model="m", prices=table, budget=budget,
                           usage=store, count_fn=len), store


def call(g, trial=0, **params):
    return g.complete(msgs(), TOOLS, params, trial)


def test_a_model_missing_from_the_table_is_refused_and_nothing_is_sent(tmp_path: Path) -> None:
    inner = Inner()
    g, _ = guard(tmp_path, inner, None, Budget(max_requests=5, max_tokens=10_000))
    with pytest.raises(UnknownModel, match="cannot be shown to be free"):
        call(g)
    assert inner.calls == 0


def test_a_paid_model_is_refused_at_zero_dollars(tmp_path: Path) -> None:
    inner = Inner()
    g, _ = guard(tmp_path, inner, PAID, Budget(max_usd=0, max_requests=5, max_tokens=10_000))
    with pytest.raises(NotFree):
        call(g)
    assert inner.calls == 0


def test_a_free_model_runs_and_costs_nothing(tmp_path: Path) -> None:
    g, _ = guard(tmp_path, Inner(), FREE, Budget(max_requests=5, max_tokens=10_000))
    call(g)
    assert (g.requests, g.tokens, g.usd) == (1, 15, 0.0)


def test_the_default_budget_allows_nothing(tmp_path: Path) -> None:
    inner = Inner()
    g, _ = guard(tmp_path, inner, FREE, Budget())
    with pytest.raises(BudgetExceeded, match="request cap"):
        call(g)
    assert inner.calls == 0


def test_the_run_request_cap_stops_the_next_call(tmp_path: Path) -> None:
    inner = Inner()
    g, _ = guard(tmp_path, inner, FREE, Budget(max_requests=2, max_tokens=10_000))
    call(g)
    call(g)
    with pytest.raises(BudgetExceeded, match="run request cap 2"):
        call(g)
    assert inner.calls == 2


def test_the_token_cap_counts_the_reserved_output_before_sending(tmp_path: Path) -> None:
    inner = Inner()
    g, _ = guard(tmp_path, inner, FREE, Budget(max_requests=5, max_tokens=100))
    with pytest.raises(BudgetExceeded, match="token cap"):
        call(g, max_tokens=500)  # 10 in + 500 reserved out > 100
    assert inner.calls == 0


def test_a_paid_model_with_a_dollar_budget_is_charged_and_capped(tmp_path: Path) -> None:
    inner = Inner(in_tok=500_000, out_tok=250_000)
    g, _ = guard(tmp_path, inner, PAID,
                 Budget(max_usd=1.0, max_requests=5, max_tokens=10_000_000))
    call(g, max_tokens=10)
    assert g.usd == pytest.approx(1.0)
    with pytest.raises(BudgetExceeded, match="usd cap"):
        call(g, max_tokens=10)


def test_daily_caps_persist_across_runs_and_reset_on_a_new_day(tmp_path: Path) -> None:
    budget = Budget(max_requests=5, max_tokens=10_000, daily_requests=2)
    g1, _ = guard(tmp_path, Inner(), FREE, budget)
    call(g1)
    call(g1)
    g2, _ = guard(tmp_path, Inner(), FREE, budget)  # a fresh run, same day
    with pytest.raises(BudgetExceeded, match="daily request cap 2"):
        call(g2)
    g3, _ = guard(tmp_path, Inner(), FREE, budget, today="2026-10-21")
    call(g3)  # the next day starts at zero


def test_daily_token_cap(tmp_path: Path) -> None:
    g, _ = guard(tmp_path, Inner(), FREE,
                 Budget(max_requests=5, max_tokens=10_000, daily_tokens=20))
    with pytest.raises(BudgetExceeded, match="daily token cap"):
        call(g, max_tokens=100)


def test_usage_file_is_written_and_readable(tmp_path: Path) -> None:
    g, store = guard(tmp_path, Inner(), FREE, Budget(max_requests=5, max_tokens=10_000))
    call(g)
    data = json.loads(store.path.read_text(encoding="utf-8"))
    assert data == {"2026-10-20": {"p": {"requests": 1, "tokens": 15}}}


def test_a_failed_call_is_not_counted(tmp_path: Path) -> None:
    class Boom:
        def complete(self, *a, **k):
            raise RuntimeError("network down")

    g, store = guard(tmp_path, Boom(), FREE, Budget(max_requests=5, max_tokens=10_000))
    with pytest.raises(RuntimeError):
        call(g)
    assert g.requests == 0 and store.today("p") == {"requests": 0, "tokens": 0}


def test_price_rows_must_be_dated_and_sourced(tmp_path: Path) -> None:
    path = tmp_path / "prices.json"
    path.write_text(json.dumps([{"provider": "p", "model": "m", "free": True}]), encoding="utf-8")
    with pytest.raises(ValueError, match="as_of"):
        PriceTable.load(path)


def test_price_table_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "prices.json"
    path.write_text(json.dumps([{"provider": "p", "model": "m", "free": True,
                                 "as_of": "2026-10-20", "source": "https://x"}]), encoding="utf-8")
    table = PriceTable.load(path)
    assert table.lookup("p", "m") is not None and table.lookup("p", "n") is None


def test_plan_flags_what_would_be_refused() -> None:
    b = Budget(max_requests=100, max_tokens=100_000, daily_requests=50)
    ok = plan(trials=10, calls_per_trial=5, input_tokens_per_call=500, output_tokens_per_call=100,
              price=FREE, budget=b)
    assert (ok.calls, ok.usd, ok.fits_run_caps, ok.days_needed) == (50, 0.0, True, 1)
    assert not ok.warnings
    big = plan(trials=60, calls_per_trial=5, input_tokens_per_call=500,
               output_tokens_per_call=100, price=FREE, budget=b)
    assert not big.fits_run_caps and big.days_needed == 6 and big.warnings
    unlisted = plan(trials=1, calls_per_trial=1, input_tokens_per_call=1,
                    output_tokens_per_call=1, price=None, budget=b)
    assert any("refused" in w for w in unlisted.warnings)
    paid = plan(trials=1, calls_per_trial=1, input_tokens_per_call=1,
                output_tokens_per_call=1, price=PAID, budget=b)
    assert any("not free" in w for w in paid.warnings)
