# ctxcheck

A test kit and flight recorder for agent context-compaction policies.

**Question:** when a harness compacts an agent's context (to fit in the window), what does the agent stop knowing, and does its behaviour change?

ctxcheck plants a "canary" — a specific rule or fact — early in a scripted trajectory, applies a compaction strategy, then grades whether the agent still acts on the canary. It runs this across multiple strategies, models, and canary types, and reports survival rates with confidence intervals.

## Status

M0 (Spine) — repo structure and tooling in place. Nothing runnable yet.

## Setup

```bash
uv sync --dev
make check   # lint + types + tests (offline)
```

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).
On Windows, run in Git Bash or install `make` via `winget install GnuWin32.Make`.

## Docs

- [`docs/PROJECT.md`](docs/PROJECT.md) — scope and goals
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — how it works
- [`docs/ROADMAP.md`](docs/ROADMAP.md) — milestones
- [`docs/LEARNING.md`](docs/LEARNING.md) — learning path (Teach-First)

## Licence

MIT
