# ARCHITECTURE — ctxcheck

Principle: **small stable seams, everything else replaceable.** The seams are the trace schema and four interfaces (Provider, Policy, CanaryPack/Grader, Runner). Everything behind them may be rewritten as understanding grows.

## Data flow

```
Scenario(seed) ──► Runner ──► Harness loop ──► Provider (via Cassette layer)
                      │            │
                      │            └─► Trace (JSONL events)  ──► runs/
                      ▼
                   Grader(trace) ─► ResultRow ─► Stats ─► results/*.json
                                                            │
                                         scripts/export ────┴─► web/public/data ─► static site
```

Nothing in the web app calls a model. The site only reads files that the Python side produced. That is what makes the playground durable.

## Repo layout

```
ctxcheck/
  CLAUDE.md  README.md  Makefile  pyproject.toml
  docs/        PROJECT PRIOR_ART ARCHITECTURE EVAL_DESIGN LEARNING ROADMAP DESIGN DECISIONS
               understanding/ (LEDGER.md + explain-backs)  notebook/  experiments/
  learn/       tiny runnable demos, one per concept (not shipped in the package)
  src/ctxcheck/
    schema/      pydantic models: events, scenario, result (SINGLE SOURCE OF TRUTH)
    tokens.py    tokenizer adapters, counting
    harness/     loop.py  tools.py  budget.py
    providers/   base.py  anthropic.py  openai_compat.py  presets.py  cassette.py  simulated.py  scripted.py
    policies/    base.py  units.py  recency.py  head_tail.py  summarize.py  mask.py
    canaries/    base.py  constraint.py  identifier.py   (history is scripted, ADR-020)
    grading/     tool_call_grader.py   (survival is judged in runner/episode.py, see ADR-020)
    runner/      episode.py  experiment.py  analysis.py  survival.py  trace_io.py
    stats/       wilson.py  paired.py   (exact McNemar, paired bootstrap, Benjamini-Hochberg)
    claims.py    checks numbers in docs against results/ (scripts/check_claims.py)
    cli.py
  tests/       unit/  property/  fixtures/  replay/
  cassettes/   recorded model responses (committed; kept small)
  runs/        sample traces (committed samples only)
  results/     versioned results JSON
  web/         Next.js (App Router, static export)
  scripts/     export_web_data.py  gen_ts_types.py  check_claims.py
  .github/workflows/
```

## Stack
- Python 3.12, `uv`, pydantic v2, typer, httpx, pytest, hypothesis (property tests), ruff, pyright.
- Web: Next.js (App Router) with static export, TypeScript, Tailwind, hand-written SVG for signature views, d3-scale for scales only.
- Types flow one way: pydantic → JSON Schema → generated TypeScript types. The web app never hand-defines a schema.
- Deploy: static hosting. No server, no database.
(Rationale and alternatives in DECISIONS.md.)

## Trace schema v0 (JSONL, one event per line)

Common fields: `schema_version`, `run_id`, `seq` (monotonic int), `ts`, `type`.

| type | key fields |
|---|---|
| `run_start` | scenario_id, seed, policy, provider, model, params, harness_git_sha, `limit_tokens` (window budget), `tools_tokens_est` (tool specs, fixed per run) |
| `message` | message_id, `step` (turn number), role, content blocks, `tokens_est` (local tokenizer), origin (`user`, `assistant`, `tool`, `summary`, `canary`) |
| `model_call` | request_hash, trial_index, model_id_reported, usage (input/output, cached if reported), cassette_hit, cost_usd |
| `tool_call` / `tool_result` | call_id, name, args / result, is_error |
| `compaction` | policy, trigger, tokens_before, tokens_after, kept_ids, dropped_ids, added_ids, cost_usd, summary_message_id, `prompt_version` (set by policies that call a model; added in 0.3) |
| `canary_planted` | canary_id, type, message_id, span, value (the planted fact) |
| `canary_probe` | canary_id, probe_message_id, grade (violated / respected / `not_applicable`; the last added in 0.3), evidence |
| `run_end` | status, `reason` (why it stopped: `end_turn`, `terminal_tool`, `max_calls`, `budget_exceeded`, `irreducible_budget`, `summary_failed`; added in 0.2), totals (`model_calls`, `summary_calls`, `steps`, `tokens_final`) |

Additions decided in LEARNING U1b (2026-10-20): `step`, `limit_tokens`, `tools_tokens_est` as above. **Canary fate is a derived view** (`src/ctxcheck/fates.py`), computed by replaying the trace. v0 rule, decided 2026-10-20: a planted fact is `kept` if its text appears verbatim in a message still in the window at the end, otherwise `gone`. Case and punctuation matter, so a paraphrase counts as gone (this undercounts survival; state it wherever the number is shown). `changed` is reserved for a labelled judge model and becomes an event only then (ADR-002). Pairing ids for control vs treatment are deferred to M4 (additive).

**Compaction ordering convention** (loop, generator and ledger all follow it): a `compaction` event is written *after* the message that triggered it and *before* the summary message it adds, so it happens inside the open step. A step's ledger row is the window at the end of that step; `after_step` is the last step closed before the compaction.

Rules:
- **Event sourcing.** The log is the source of truth. Any view (token ledger, strata, loss diff) is *derived* by replaying events. (This is the DDIA log-as-truth idea; learn it in unit U2.)
- **Versioning.** Additive changes bump the minor version. Breaking changes bump the major version and ship a migration script. The web app refuses an unknown major.
- Record **both** `tokens_est` (local) and provider-reported usage; the difference is itself something to understand (unit U0).

## Interfaces (Python Protocols)

```python
class Provider(Protocol):
    def complete(self, messages: list[Message], tools: list[ToolSpec],
                 params: Params, trial_index: int) -> ModelResponse: ...

class Policy(Protocol):
    name: str
    def apply(self, history: list[Message], budget_tokens: int,
              ctx: PolicyContext) -> CompactionResult: ...
    # CompactionResult: new_history, dropped_ids, added_ids, tokens_before, tokens_after, cost_usd
    # Deterministic policies are PURE. LLM policies receive a Provider via ctx.

class CanaryPack(Protocol):
    name: str
    def build(self, seed: int) -> Scenario: ...
    # Scenario: turns[], planted[], probe_request, grader

class Grader(Protocol):
    def grade(self, trace: Trace) -> GradeResult: ...   # violated: bool, evidence: str
```

### Policy invariants (these become property tests; understand each)
1. `tokens_after ≤ budget_tokens` unless irreducible (system + last turn exceed budget); then raise a clear error, never silently overrun.
2. **Tool pairing:** a `tool_call` is never kept without its `tool_result`, and vice versa. (Providers reject orphans; this is a classic compaction bug.)
3. Message order is preserved among kept messages.
4. Deterministic policies are pure and idempotent: applying again when already under budget changes nothing.
5. `dropped_ids ∪ kept_ids` equals the input ids; nothing disappears unrecorded.

## Providers and cassettes

- `Provider` adapters: Anthropic and an OpenAI-compatible adapter (covers many hosted and local models). Adding one is a single file.
- **Cassette layer** wraps any provider. Modes: `record`, `replay` (a miss is an error, always in CI), `auto` (a miss calls the provider only if the budget guard allows).
- **Cassette key** = sha256 of canonical JSON of `{provider, model, params, messages, tools, trial_index}`. "Canonical" means `json.dumps(obj, sort_keys=True, ensure_ascii=False)` — key ordering must be pinned or the hash diverges across Python versions and libraries.
  - `trial_index` is in the key on purpose. At temperature > 0, n trials need n distinct recordings; without it every "trial" replays the same output and your variance is fake. (Learn this; it is a gate.)
  - Store the response, usage, the model id the provider *reported*, the date, and library versions.
- Replays must never silently fall through to the network in CI.

## Budget guard
- `ctxcheck run --dry-run` prints planned calls, estimated tokens and cost from a user-supplied, dated price table. Prices are never hard-coded.
- `--max-usd` is a hard cap checked before every live call. Exceeding it aborts and keeps partial results.
- Cost per call is recorded in the trace.

## Runner
- Executes the matrix `scenario × policy × model × trial`. Each cell has a stable key; results append as JSONL rows so a crash resumes without redoing or double-counting.
- Seeds make scenarios reproducible: filler content and planted values are generated deterministically from the seed.

## Results format
`results/<exp_id>/<date>-<git_sha>.json` containing: `schema_version`, experiment id, git sha, model ids reported, date, params, per-cell counts (n, k), intervals, paired comparisons, links to run ids. **Never overwrite**; new runs add files.

## Web data
`scripts/export_web_data.py` turns `runs/` and `results/` into static JSON under `web/public/data/` plus an index. Run files are lazy-loaded. The recorder derives all views client-side from events. A user-supplied trace file is parsed in the browser and never uploaded anywhere.

## Security notes (these double as research hooks)
- The summarizer is an untrusted-input sink: tool outputs flow into the compaction prompt. A canary pack for compaction-targeted injection is a Later item; do not build it in v0.1, but design the `llm_summary` policy so the compaction prompt is an explicit, logged, versioned artifact.
- No keys in the repo or in cassettes. A pre-commit check scans for key patterns.

## CI (GitHub Actions)
`make check` on every push (offline), web build, schema drift check (pydantic ↔ generated TS), and a replay-only smoke experiment. Live runs are manual (`workflow_dispatch`) with a secret and an explicit cap.

## What to change when things evolve
- New policy / canary pack / provider: add one file implementing the Protocol, add tests, register it.
- Schema change: edit the pydantic model, bump version, regenerate types, add migration if breaking.
- Anything that violates a seam: write an ADR first.
