# CLAUDE.md — ctxcheck

Working name. A test kit and flight recorder for agent context-compaction policies. Question: when a harness compacts context, what does the agent stop knowing, and does behaviour change? Read `docs/PROJECT.md` for the why.

**Keep this file short. Detail lives in `docs/`. Open the doc you need; do not preload everything.**

## Docs index
- `docs/PROJECT.md` scope, non-goals, success criteria
- `docs/PRIOR_ART.md` what exists, what is verified, open verification tasks
- `docs/ARCHITECTURE.md` components, trace schema, interfaces, repo layout
- `docs/EVAL_DESIGN.md` canaries, conditions, graders, statistics, threats to validity
- `docs/LEARNING.md` concept map, Teach-First Protocol, gates
- `docs/ROADMAP.md` milestones with exit criteria, scope fence, Later list
- `docs/DESIGN.md` web identity, views, interaction rules
- `docs/DECISIONS.md` ADRs (append-only)
- `design/SITE_RULES.md`, `design/VIDEO_RULES.md` banned looks, motion system, honesty rules: read before any web or video work
- `design/PROGRESS.md` design-subsystem gates and the exact next step
- `docs/understanding/` my explain-backs and `LEDGER.md` (gates passed)
- `docs/notebook/` lab notebook (failures included)
- `docs/experiments/` preregistrations

## Commands
- `make check` lint + types + tests (offline) + secrets scan — run this after every change
- `make test` tests only, replay mode, no network
- `make web` run the web app locally
- `make export` regenerate `web/public/data` from `results/` and `runs/`
- `ctxcheck run --dry-run ...` always before a live run

## Setup (once, after cloning)
```
uv sync --dev
```

## Rules that cannot be broken
1. **Teach-First Protocol** for all code in `src/ctxcheck/` (see `docs/LEARNING.md`). No moving past an unpassed gate.
2. **No number without an artifact.** Every figure in docs/UI comes from `results/` or `runs/`. Unsure = verify or tag `[unverified]`.
3. **Preregister** experiments before running them.
4. **Pivot protocol:** direction changes need an ADR + doc updates + notebook entry. No silent divergence.
5. **Scope fence:** out-of-scope ideas go to Later in `docs/ROADMAP.md`, not into code.
6. **Offline tests.** Live model calls need `--max-usd` and a dry-run first. Secrets never committed.
7. **Two-sided tests** for every grader/detector (must fire / must not fire).
8. **Small diffs.** Over ~150 lines needs an approved plan. Commits conventional and explainable by me.
9. **Recorded vs simulated** must always be labelled in UI and docs.

## Layout (details in ARCHITECTURE.md)
`src/ctxcheck/{schema,harness,providers,policies,canaries,grading,runner,stats}` · `tests/` · `cassettes/` · `runs/` · `results/` · `web/` · `learn/` · `scripts/`

## Style
Python 3.12, type-hinted, pydantic v2 models as the single source of truth for schemas. Readable over clever. Comments say why, not what.
