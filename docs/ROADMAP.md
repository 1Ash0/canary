# ROADMAP — ctxcheck

No dates. Milestones have **exit criteria**; units (see LEARNING.md) are sized by understanding. If studies or grades need the time, pause; the roadmap is a sequence, not a schedule.

## Pace rules
- Cap weekly hours explicitly (decide yours; write it in `docs/notebook/`). If grades slip, the project pauses, not the grades.
- A milestone is "done" only when exit criteria hold **and** its gates are passed.
- Prefer a thin vertical slice that works end to end over a deep layer that cannot be seen.

## Status check (2026-10-20, against the exits below, with evidence; refreshed after the M2 to M5 build)
| Milestone | State | Evidence |
|---|---|---|
| M0 Spine | **done** | `make check` passes offline; 8/8 PRIOR_ART tasks answered (notebook 2026-10-19); ledger M0 row |
| Learning units U0–U5 | **done** (ahead of the milestones that list their gates) | `learn/*.py` demos; G0–G5 in LEDGER |
| M1 First light | **in progress** (updated 2026-10-20) | DONE: trace schema v0 (9 event types, 23 tests); token ledger; real-tokenized synthetic fixture (160 events); canary fates; Wilson in `src/`; labelled mock experiment (control vs recency_truncate, 10 trials); export pipeline; site with hero, mock experiment and recorder with step permalinks (11 behaviours verified). README hero and positioning paragraph (product exits 2 and 4, 2026-10-20). TODO: the owner's decision on deploying and the `ctxcheck` PyPI recheck before any public URL; the owner's acceptance of the Teach-First gates for what was built (see LEDGER) |
| M2 Harness and replay | **built offline; live part waits on the owner** | DONE: loop, tools, scripted provider, Anthropic and OpenAI-compatible adapters, budget guard (U9), cassettes in `src/` (U10), trace writer, CLI `plan` `add-price` `smoke` `run` `report`; the exit test records through cassettes and replays byte-identically except `cassette_hit` (`tests/replay/test_m2_exit.py`). WAITING ON OWNER: a free-tier key in the shell, `ctxcheck smoke`, the first live call; gates G8, G9, G10 |
| M3 Policies | **built offline; gate pending** | four policies with property tests for the five invariants, ADR-019; the deterministic survival grid and page. NOT BUILT: re-applying a policy to a recorded run in the browser (stretch; needs a recorded run, now under Later). Gate G11 |
| M4 Canaries + first measurement | **built offline; nothing measured** | constraint and identifier packs, two-sided grader, exact McNemar, paired bootstrap, Benjamini-Hochberg, resumable runner, simulated agent (labelled), EXP-001 drafted. NOT DONE: freezing and running EXP-001; the measured result and its heatmap of behaviour. Gates G12, G13, and revisit G7 |
| M5 Rigor and write-up | **partly built** | `check_claims.py` in CI, threats to validity extended, EXP-002 and EXP-003 drafted, CI covers design tests, site build and export drift. NOT DONE: EXP-002 and EXP-003 runs, counterfactual-fork view (needs recorded runs), v0.1 tag (not before a measured result exists), posts |
| M6 | not started | — |
| Design subsystem (`design/`) | D0–D4 approved, D4b built; **paused after D4b** so site and video build on real data (see `design/PROGRESS.md`) | tokens, rules, scene module, hero motion, tests |

## Milestones

### M0 — Spine
Repo, docs in place, `make check`, CI skeleton, secrets scan, working-name decision (ADR-009), PRIOR_ART verification tasks done and recorded.
Exit: a fresh clone passes `make check` offline; PRIOR_ART open tasks answered; first ledger entry exists.
Units: U0 (token ledger can come right after).

### M1 — First light (vertical slice, public)
Trace schema v0, token ledger on a **synthetic but real-tokenized** fixture session, flight recorder web view (strata view only), step permalinks, deployed static site.
Exit: a public URL; a stranger opens a run, scrubs steps, copies a permalink to one step. No API key anywhere.

**Product exits (all required before M1 is done):**
1. **Name confirmed.** Run `pip index versions ctxcheck` (or `pip install ctxcheck --dry-run`). If taken, pick a new name and update all refs before publishing anything. A name change after a public URL exists is painful.
2. **README hero.** First screen of README states the problem with a number: ConstraintRot's finding that one compaction raises pooled violation from 0% to 30% (Chen, arXiv 2606.22528v2; tagged `[reproduced by third party]`; corrected from "37%" on 2026-10-20, see PRIOR_ART), what ctxcheck measures, and one playground screenshot. No install required to understand what the tool does.
3. **Playground ships with a complete mock experiment.** At minimum: two conditions (control vs recency_truncate), 10 mock trials, violation rate with Wilson interval, strata view showing one dropped canary highlighted in red. A visitor sees a real result before touching the CLI.
4. **Positioning copy.** One paragraph above the fold: who this is for, what it reveals, why the confidence intervals matter. Not a feature list.

Post 1 (tag `built`): the recorder and what surprised you about where tokens go. Ask only genuine questions.

### M2 — Harness and replay
Own harness loop, tools, provider adapters, cassettes, budget guard, deterministic replay. The recorder now renders a **real** run.
Exit: one scripted scenario runs live under a cap, is recorded, and replays offline byte-for-byte in a test. Gates G1, G2.

### M3 — Policies
`recency_truncate`, `head_tail`, `llm_summary`, `observation_mask`, with property tests for the five invariants. The recorder shows policy effects; deterministic policies can be re-applied to a recorded run in the browser (label: **simulated**).
Exit: all invariants pass under property tests; the UI clearly separates recorded from simulated. Gate G3.

### M4 — Canaries and first measurement
`constraint` and `identifier` packs with two-sided grader fixtures, runner with resume, stats module, EXP-001 preregistered and run, survival heatmap page.
Exit: a measured result with intervals reproducible from cassettes with one command, replicate or honest null. Gates G4, G5.
Post 2 (tag `measured` or `broke`): the replication and what it did or did not show.

### M5 — Rigor and write-up
EXP-002 and EXP-003, optional EXP-004, `check_claims.py` in CI, threats-to-validity section, counterfactual-fork view, README and lab notebook polished, v0.1 tag.
Exit: README alone lets a stranger reproduce the headline result and add a policy file.
Post 3 (tag `measured`): the policy comparison and dose-response curve with intervals.

### M6 — Productize
CLI plugin loading (`ctxcheck run --policy ./mine.py --pack constraint`), example GitHub Action, packaging, docs for contributors.
Exit: `pip install` works and a user's own policy file runs against a pack and gates CI.

## Scope fence (v0.1 = M0 to M5; M6 optional but intended)
Anything not in PROJECT.md "In" goes to Later below with a trigger. Do not build Later items "while you're there".

## Later (with triggers, not promises)
| Item | Trigger to start |
|---|---|
| Pinning, offload, reset+handoff policies | v0.1 shipped and EXP-002 done |
| Re-apply a deterministic policy to a recorded run in the browser (labelled `simulated`); counterfactual-fork view | A recorded run exists (the M3 stretch and M5 view were deferred because there is nothing recorded to re-apply them to) |
| Progressive compaction (summary of a summary, drift over rounds) | EXP-001 outcome is understood; needs the loop to compact mid-history instead of once at the probe (ADR-020) |
| Crossed compactor and agent models (EXP-004) | Two free models pass `ctxcheck smoke` and EXP-001 is reported |
| Canary packs: failed_approach, decision_rationale, preference, execution_state, superseded_fact | After EXP-001 outcome is understood; pick by what real harnesses seem to forget |
| Import real session logs (Claude Code/Codex JSONL) to trace v0 | A concrete user or post comment asks for it, and the trace schema is stable |
| MCP wrapper (`run_canaries`, `explain_loss`) | M6 shipped |
| Compaction-targeted injection pack | EXP-001 done and a threat model is written |
| Slipstream-style async validation as a policy | After TRACE/ARC/Slipstream are read in full and you can state what is novel to add |
| Adapter for a real harness's compaction hook (Pydantic AI, Strands) | M6 shipped, and you have read that harness's compaction code |
| Integration with your other two projects (tool-surface lab, telemetry probes) via the shared trace schema | Each project stands alone first; integrate only when both have a stable v0.1 |
| Upstream contribution (e.g. canary cases as an eval in a harness repo) | A maintainer agrees on scope in an issue first; no unsolicited PRs |

## Pivot protocol
Direction changes (from results, new papers, or learning) follow: write ADR in DECISIONS.md → update affected docs → notebook entry → then code. A killed idea is documented, not deleted. Pivot triggers worth watching:
- PRIOR_ART verification shows an existing practitioner tool equivalent to ours: re-scope the tool/playground layers.
- EXP-001 is a clean null: investigate scenario realism, then decide whether to extend or reframe the project around the null.
- Costs exceed the cap: reduce models/trials, not rigor.

## Evolution hooks already in place
Stable seams (trace schema, four interfaces) · plugin-by-file · versioned results · cassettes. These are what allow the project to grow without rewriting.

## Posting cadence and honesty
Three posts (M1, M4, M5). Each: one idea, one diagram or screenshot, epistemic tag, a permalink to the exact step shown, and the limits stated up front. Draft posts in `docs/notebook/`.
