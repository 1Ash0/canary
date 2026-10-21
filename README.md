# Canary

**See what compaction forgets.** Live: https://canary-brown.vercel.app. A flight recorder and canary lab for agent context compaction. The Python package and CLI are called `ctxcheck`.

When an agent's context fills up, the harness compacts it, and the agent carries on with a summary. One published benchmark found that a single compaction step took rule violations from 0% to 30% pooled across seven models, and as high as 59% on the worst two. In that benchmark, nothing crashed: the agent kept working, confidently, without a rule it had been given. *(Chen, [arXiv 2606.22528](https://arxiv.org/abs/2606.22528) v2, abstract. Reported by the paper. On our harness the effect appears with one of two free models; see below.)*

![The Canary recorder showing a synthetic run: the context window by step, three planted facts, one compaction, and the fate of each fact](docs/img/playground.png)

*The recorder on a **synthetic fixture** (generated test data, not a real agent run). Each bar is the context window at one step. Dots are planted facts. After the compaction line, one fact is kept and two are gone.*

## Who it is for, and what it shows

If you build or tune an agent harness and have to decide how its context gets compacted, you currently find out what a policy forgot by noticing a bad action much later. Canary makes that visible. It plants facts early in a scripted run, compacts the context with the policy under test, asks the agent to do something where a fact matters, and grades the tool call it emits. You see which facts survived, which were dropped, and whether behaviour changed. Every rate comes with a confidence interval, because with the ten or thirty trials an experiment can afford, a bare percentage is hard to tell from noise, and an interval says how much weight it can bear.

## Where it stands

**The machinery is built and tested offline, and four preregistered experiments have run live on free models.**
- **EXP-001** (does one summary make the agent break a rule?): split by the model writing the summary. NVIDIA's `gpt-oss-20b` shows the published effect, Mistral's `ministral-14b-latest` shows none; Groq's re-run is unfinished and Gemini's summaries failed the validity check. **No cross-model replication is claimed.** The owner's hand audit found behaviour followed what the summary kept. [`docs/experiments/EXP-001.md`](docs/experiments/EXP-001.md)
- **EXP-001b** (the `gpt-oss-20b` result with its confound removed: its reasoning had been eating the summary's token cap): the effect replicates with no summary cut off, and a length-matched control shows a shorter window alone does not explain it. [`docs/experiments/EXP-001b.md`](docs/experiments/EXP-001b.md)
- **EXP-002** (four policies, two canaries, same seeds): dropping the oldest turns loses an early rule and the agent guesses; keeping head and tail, or masking tool output, leaves it as good as full context; a model summary sits in between and depends on the model. [`docs/experiments/EXP-002.md`](docs/experiments/EXP-002.md)
- **EXP-004** (three facts at three depths of one history, one request per fact): which policy is safe depends on where the fact sits. Dropping the oldest turns loses the early rule, keeping head and tail loses the middle and late facts, and each time the agent fails on exactly the fact that was lost. EXP-002's safe-looking head-and-tail was a property of a rule planted at turn 2. [`docs/experiments/EXP-004.md`](docs/experiments/EXP-004.md)

Every number, every deviation from the plan, and everything that went wrong is in those Results sections, generated from `results/` and checked by `scripts/check_claims.py`.

| Works now | Not yet |
|---|---|
| Trace schema 0.4, token ledger and per-fact fates, derived by replaying a trace | Groq at the planned 27 seeds (EXP-001 and EXP-001b) |
| Agent loop with a budget check, two provider adapters (Anthropic, OpenAI-compatible), record/replay cassettes, a budget guard that refuses anything not provably free, live runs on free Groq, Gemini, Mistral and NVIDIA models | A summary result that holds across models, or a prompt that keeps the rule |
| Four policies: `recency_truncate`, `head_tail`, `observation_mask`, `llm_summary` (versioned prompt), with property tests for the five invariants | Progressive compaction (history is scripted and compacted once, at the probe) |
| Canary packs: `constraint`, `identifier`, and `multi_*` (three facts at three depths, one graded per request), a tool-call grader tested on both sides, four conditions per seed, a resumable runner, exact McNemar, paired bootstrap, Benjamini-Hochberg, a summary-validity flag | EXP-003 (dose-response: the window budget): draft only |
| A **deterministic** survival grid: what each policy keeps (real policy code on seeded histories, no model) | The owner's blind audits of the EXP-001b and EXP-002 summaries (sheets in `docs/audit/`) |
| A static site in four linked chapters: a Lab (one rule or three facts) where you compact a real history yourself and see what a real model did with that window; a comparison of any two recorded ways of making room on the same seed, with the tool call each agent made; results for every experiment, each mark opening its episode; the method. Plus a recorder with a text view and transcript | (deployed: https://canary-brown.vercel.app) |

### What the survival grid shows

Planting a rule at the first turn of an 18-turn history and compacting to a budget: under recency truncation the rule is gone in every history we tried (0 of 20 histories at 3,600 tokens), while head-and-tail keeps it (20 of 20 at the same budget). That says what a policy keeps. It does not say what an agent does next; that needs a model. The numbers are in [`results/survival/grid.json`](results/survival/grid.json) and are checked against the docs by `scripts/check_claims.py`.

Every number traces to a file under `runs/` or `results/` and says whether it is `synthetic fixture`, `mock data`, `deterministic`, `simulated` or `recorded`.

## Run it

```bash
git clone https://github.com/1Ash0/canary.git && cd canary
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
