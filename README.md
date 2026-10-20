# Canary

**See what compaction forgets.** A flight recorder and canary lab for agent context compaction. The Python package and CLI are called `ctxcheck`.

When an agent's context fills up, the harness compacts it, and the agent carries on with a summary. One published benchmark found that a single compaction step took rule violations from 0% to 30% pooled across seven models, and as high as 59% on the worst two. In that benchmark, nothing crashed: the agent kept working, confidently, without a rule it had been given. *(Chen, [arXiv 2606.22528](https://arxiv.org/abs/2606.22528) v2, abstract. Reported by the paper; we have not yet reproduced it.)*

![The Canary recorder showing a synthetic run: the context window by step, three planted facts, one compaction, and the fate of each fact](docs/img/playground.png)

*The recorder on a **synthetic fixture** (generated test data, not a real agent run). Each bar is the context window at one step. Dots are planted facts. After the compaction line, one fact is kept and two are gone.*

## Who it is for, and what it shows

If you build or tune an agent harness and have to decide how its context gets compacted, you currently find out what a policy forgot by noticing a bad action much later. Canary makes that visible. It plants facts early in a scripted run, compacts the context with the policy under test, asks the agent to do something where a fact matters, and grades the tool call it emits. You see which facts survived, which were dropped, and whether behaviour changed. Every rate comes with a confidence interval, because with the ten or thirty trials an experiment can afford, a bare percentage is hard to tell from noise, and an interval says how much weight it can bear.

## Where it stands

**The machinery is built and tested offline, and one pilot has been run on real free-tier models.** EXP-001 (frozen before running) did **not replicate** the published effect at this scale: 10 seeds, two models that actually summarise, one prompt. It is a pilot, not a result about models in general; the Results section of [`docs/experiments/EXP-001.md`](docs/experiments/EXP-001.md) has every number and the things that went wrong. The manual audit of summaries is still owed.

| Works now | Not yet |
|---|---|
| Trace schema 0.3, token ledger and per-fact fates, derived by replaying a trace | Anything at the planned 27 seeds per cell |
| Agent loop with a budget check, two provider adapters (Anthropic, OpenAI-compatible), record/replay cassettes, a budget guard that refuses anything not provably free, live runs on free Groq, Gemini and Mistral models | A replication of the published effect, or a clean null |
| Four policies: `recency_truncate`, `head_tail`, `observation_mask`, `llm_summary` (versioned prompt), with property tests for the five invariants | Progressive compaction (history is scripted and compacted once, at the probe) |
| Two canary packs (`constraint`, `identifier`), a tool-call grader tested on both sides, four conditions per seed, a resumable runner, exact McNemar, paired bootstrap, Benjamini-Hochberg | EXP-002 (policy comparison) and EXP-003 (dose-response): drafts only |
| A **deterministic** survival grid: what each policy keeps (real policy code on seeded histories, no model) | A public URL |
| A static site: landing page, run recorder with step permalinks, survival page, about | The site still shows only synthetic and deterministic data, not the EXP-001 results |

### What the survival grid shows

Planting a rule at the first turn of an 18-turn history and compacting to a budget: under recency truncation the rule is gone in every history we tried (0 of 20 histories at 3,600 tokens), while head-and-tail keeps it (20 of 20 at the same budget). That says what a policy keeps. It does not say what an agent does next; that needs a model. The numbers are in [`results/survival/grid.json`](results/survival/grid.json) and are checked against the docs by `scripts/check_claims.py`.

Every number traces to a file under `runs/` or `results/` and says whether it is `synthetic fixture`, `mock data`, `deterministic`, `simulated` or `recorded`.

## Run it

```bash
uv sync --dev
make check                              # lint, types, offline tests, secrets scan, claims check
uv run ctxcheck survival                # the deterministic survival grid (no model, no key)
uv run ctxcheck run --exp EXP-DEMO --simulated --seeds 10   # the whole pipeline with a toy agent
uv run ctxcheck report results/simulated/EXP-DEMO           # intervals and paired tests (labelled SIMULATED)
make export                             # results and traces -> web/public/data
npm --prefix web install && make web    # the site at http://localhost:3000
```

The `--simulated` agent follows a rule only if it can still read it. It exists to exercise the pipeline for free, its output lives in `results/simulated/`, and every command labels it **not measured**.

### A live run (free models only)

Live calls cost nothing by design (ADR-018): the budget guard refuses any model not marked free in a dated price table, and caps requests and tokens per run and per day. Keys are read from environment variables, never from arguments.

```bash
export OPENROUTER_API_KEY=...           # set in your shell, never in a file or in chat
uv run ctxcheck add-price --preset openrouter --model <id>:free --free --source <provider page>
uv run ctxcheck smoke --preset openrouter --model <id>:free       # does this model call tools?
uv run ctxcheck run --exp EXP-001 --preset openrouter --model <id>:free --seeds 10 \
  --max-requests 50 --max-tokens 500000 --dry-run                 # always first
```

Remove `--dry-run` to record. Cassettes are written as it goes, so an interrupted run resumes without repaying for finished calls, and a replay (`--mode replay`) spends nothing. Only synthetic, seeded scenarios are ever sent.

Requires Python 3.12+, [uv](https://docs.astral.sh/uv/) and Node 22. On Windows, use Git Bash or `winget install GnuWin32.Make`, or run `.\check.ps1` instead of `make check`.

## Limits worth knowing before trusting any result

- A planted rule in a synthetic history is not a rule from a real organisation. Results speak to arbitrary rules, an upper bound on decay, not a general violation rate.
- History is scripted and compacted once, at the probe. Real sessions compact progressively.
- The model that writes the summary is the model that acts on it; crossing them is a later experiment.
- Free models change and disappear; every result records the model id the provider reported and the date.
- Pilot-scale n: reports state the achieved n per cell, and intervals will be wide.

The full list, with the instrument and statistical threats, is in [`docs/EVAL_DESIGN.md`](docs/EVAL_DESIGN.md#7-threats-to-validity-a-living-list-add-to-it).

## Docs

- [`docs/PROJECT.md`](docs/PROJECT.md) scope, non-goals and success criteria
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) the trace schema and how the pieces fit
- [`docs/EVAL_DESIGN.md`](docs/EVAL_DESIGN.md) canaries, conditions, grading and statistics
- [`docs/experiments/`](docs/experiments/) preregistrations (drafts until frozen)
- [`docs/DECISIONS.md`](docs/DECISIONS.md) the decisions, including what each one costs
- [`docs/PRIOR_ART.md`](docs/PRIOR_ART.md) what exists and how much of it has been read
- [`docs/ROADMAP.md`](docs/ROADMAP.md) milestones, with a dated status check
- [`design/`](design/PROGRESS.md) the design system, tokens and motion rules for the site

## Licence

MIT
