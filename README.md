# Canary

**See what compaction forgets.** A flight recorder and canary lab for agent context compaction. The Python package and CLI are called `ctxcheck`.

When an agent's context fills up, the harness compacts it, and the agent carries on with a summary. One published benchmark found that a single compaction step took rule violations from 0% to 30% pooled across seven models, and as high as 59% on the worst two. In that benchmark, nothing crashed: the agent kept working, confidently, without a rule it had been given. *(Chen, [arXiv 2606.22528](https://arxiv.org/abs/2606.22528) v2, abstract. Reported by the paper; we have not yet reproduced it.)*

![The Canary recorder showing a synthetic run: the context window by step, three planted facts, one compaction, and the fate of each fact](docs/img/playground.png)

*The recorder on a **synthetic fixture** (generated test data, not a real agent run). Each bar is the context window at one step. Dots are planted facts. After the compaction line, one fact is kept and two are gone.*

## Who it is for, and what it shows

If you build or tune an agent harness and have to decide how its context gets compacted, you currently find out what a policy forgot by noticing a bad action much later. Canary makes that visible. It plants facts early in a scripted run, compacts the context with the policy under test, asks the agent to do something where a fact matters, and grades the tool call it emits. You see which facts survived, which were dropped, and whether behaviour changed. Every rate comes with a confidence interval, because with the ten or thirty trials an experiment can afford, a bare percentage is hard to tell from noise, and an interval says how much weight it can bear.

## Where it stands

Early, and honest about it. **M1 ("first light") is in progress.**

| Works now | Not yet |
|---|---|
| The trace schema (9 event types), a token ledger, and per-fact fates, all derived by replaying a trace | The agent loop, provider adapters and recorded model runs (M2) |
| A seeded synthetic session with real token counts, labelled `synthetic fixture` | Compaction policies as code in `src/` (M3) |
| Wilson intervals, and a **mock** experiment (control vs `recency_truncate`, 10 trials, simulated outcomes at assumed rates, labelled `mock data`) | Any measured result (M4) |
| A static site: landing page, run recorder with step permalinks, about | A public URL |

Nothing here has called a model. Every number on the site traces to a file under `runs/` or `results/`, and says whether it is synthetic, mock or recorded.

## Run it

```bash
uv sync --dev
make check                              # lint, types, offline tests, secrets scan
uv run python -m ctxcheck.synthetic     # regenerate the synthetic run
make export                             # trace -> web/public/data
npm --prefix web install && make web    # the site at http://localhost:3000
```

Requires Python 3.12+, [uv](https://docs.astral.sh/uv/) and Node 22. On Windows, use Git Bash or `winget install GnuWin32.Make`, or run `.\check.ps1` instead of `make check`.

## Docs

- [`docs/PROJECT.md`](docs/PROJECT.md) scope, non-goals and success criteria
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) the trace schema and how the pieces fit
- [`docs/EVAL_DESIGN.md`](docs/EVAL_DESIGN.md) canaries, conditions, grading and statistics
- [`docs/PRIOR_ART.md`](docs/PRIOR_ART.md) what exists and how much of it has been read
- [`docs/ROADMAP.md`](docs/ROADMAP.md) milestones, with a dated status check
- [`design/`](design/PROGRESS.md) the design system, tokens and motion rules for the site

## Licence

MIT
