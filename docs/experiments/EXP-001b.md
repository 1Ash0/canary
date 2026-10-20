# EXP-001b — EXP-001 for reasoning models, with a summary cap their reasoning cannot eat

Status: **frozen before any run** (this file is committed before the first EXP-001b call; the commit hash is recorded below in a follow-up commit).
Frozen at commit: b5cc18f
Epistemic tag of results: `measured` (recorded model output only)

## Why this exists
The owner's audit of EXP-001 found that `gpt-oss` models reason before they answer, and the reasoning counts against the summary token cap. Under EXP-001's `max_summary_tokens=400`, many of their summaries were cut off, and cut-off summaries lost the rule more often (EXP-001, "Owner audit of the NVIDIA summaries"). So EXP-001's NVIDIA result mixes two things: summaries that drop the rule, and summaries that are truncated. This experiment repeats EXP-001 for those models with a summary call configured so truncation should be rare, so the result says something about the model, not the cap.

## What was verified before freezing (2026-10-21)
- Groq's reasoning docs (console.groq.com/docs/reasoning) list `reasoning_effort` with values `low`, `medium`, `high` for GPT-OSS 20B and 120B, and warn that the default `max_completion_tokens` "may be too low for complex reasoning".
- Live calls on 2026-10-21: Groq `openai/gpt-oss-120b` and NVIDIA `openai/gpt-oss-20b` both accepted `reasoning_effort: "low"` and answered a one-sentence question within a small number of completion tokens; NVIDIA rejected `"none"`; NVIDIA with `"high"` and a 400-token cap spent the whole cap reasoning and returned no text (the EXP-001 failure in miniature).

## Question
For `gpt-oss` models, when summaries are complete, does compaction with a generic summary (`llm_summary`, prompt v1) still make the agent break a standing rule more often than full context (`control`) and a same-length uncompacted window (`length_matched`)?

## Hypotheses
- **H1** (as EXP-001) treatment violates more than control, and more than length_matched, per model.
- **H2** (instrument) with the new summary settings, fewer than 10% of summaries are cut off by the cap.
- Expectation, not a claim: with complete summaries the effect for `gpt-oss-20b` will be smaller than in EXP-001, because part of EXP-001's effect came from truncation; whether it disappears is the open question.

## Design (everything as EXP-001 except the summary call)
- Pack `constraint`; conditions `floor`, `control`, `length_matched`, `treatment`; policy `llm_summary`, prompt `v1`, `keep_units=2`; window limit 2400 tokens; one trial per seed; provider-default temperature; synthetic seeded scenarios only.
- **Changed:** the summary call only (not the agent's calls) is sent with `reasoning_effort: "low"` and `max_summary_tokens=1200`. Low effort keeps reasoning short; the larger cap leaves room for a complete summary after it. Summary length is still bounded by the prompt ("Be concise"), which is unchanged.
- **Models:** NVIDIA `openai/gpt-oss-20b` (27 seeds), and Groq `openai/gpt-oss-120b` (seeds 1 upward until its daily token limit stops the run; the achieved n is reported, and later days may extend it to 27 without any change to this design). Floor, control and length-matched cells are re-run fresh for these models.
- **Reference:** Mistral `ministral-14b-latest` does not reason before answering and never reached the cap in EXP-001, so it is not re-run; EXP-001's Mistral result is the reference.
- **Recorded per episode:** the summary call's finish reason (schema 0.4), so truncation is measured, not inferred.

## Primary comparisons
Per model: treatment vs control, treatment vs length_matched, paired by seed. Benjamini-Hochberg across the primary comparisons of this experiment.

## Analysis plan, validity checks and interpretation rules
As EXP-001, including addendum A's reporting rule (a model with more than 30% invalid summaries is reported as "summarizer failed" and does not count toward a verdict) and the requirement that a replication needs both a bootstrap interval excluding zero and an adjusted exact McNemar q below 0.05. In addition:
- **Instrument check:** if 10% or more of a model's summaries are cut off (finish reason `length`), that model's result is reported as "still truncation-limited" and is not used to argue about the model.
- **Comparison with EXP-001 (exploratory):** the treatment violation rate here versus EXP-001's for `gpt-oss-20b`, reported descriptively with both intervals. No test is preregistered for it, because the conditions differ in more than one way (new fresh floor and control samples too).

## What would make us stop
Daily provider limits. No stopping on interim results.

## Manual audit
The owner reads at least 20 EXP-001b summaries (sheet generated after the run).

## Results

Recorded 2026-10-20; source `results/EXP-001b/summary.json` (regenerate with `ctxcheck report results/EXP-001b`, then `python scripts/write_results.py EXP-001b`). 108 episodes. Epistemic tag: `recorded`. Every number below is generated from the summary and checked by `scripts/check_claims.py`.

| Model | Condition | Broke the rule | 95% interval | No summary | Cut off | Invalid summary |
|---|---|---|---|---|---|---|
| `openai/gpt-oss-20b` | control | 1/27 | 1%–18% | 0 | – | – |
| `openai/gpt-oss-20b` | floor | 25/27 | 77%–98% | 0 | – | – |
| `openai/gpt-oss-20b` | length_matched(llm_summary) | 0/27 | 0%–12% | 0 | – | – |
| `openai/gpt-oss-20b` | treatment(llm_summary) | 12/27 | 28%–63% | 0 | 0 of 27 | 0 of 27 |

### Comparisons
- `openai/gpt-oss-20b`, treatment(llm_summary) vs control: 12 versus 1 discordant pairs of 27, risk difference +41% (95% bootstrap +19% to +63%), exact McNemar p = 0.0034, BH q = 0.0034.
- `openai/gpt-oss-20b`, treatment(llm_summary) vs length_matched(llm_summary): 12 versus 0 discordant pairs of 27, risk difference +44% (95% bootstrap +26% to +63%), exact McNemar p = 0.00049, BH q = 0.00098.

### Verdict by the preregistered rules
- **Instrument check (H2): passed.** Summaries cut off by the cap: none (see the table), against 9 of 24 judged summaries in EXP-001 under the 400-token cap. No summary failed to be produced.
- **H1 for `gpt-oss-20b`: replicates.** Both primary comparisons have a positive paired difference whose bootstrap interval excludes zero, and an adjusted exact McNemar q below 0.05. Validity checks hold: floor broke the rule in 25 of 27, control in 1 of 27, and no cell had episodes without a summary.
- **Groq `gpt-oss-120b`: no episodes yet.** Its daily token limit was spent on the same day by earlier runs; the design allows later days to add seeds. Nothing is claimed for it.

### What it means
- EXP-001's NVIDIA effect was not an artefact of truncation. With every summary complete, the treatment rate is still 12 of 27, while the same-length uncompacted window broke the rule in 0 of 27: the loss comes from what the summary leaves out, not from a shorter window.
- Exploratory: the channel name survived in 13 of 27 summaries, and behaviour matched survival in 25 of 27 episodes; the mismatches are agents that lost the rule and still picked the right channel, which the floor condition says happens by chance about one time in four.
- Together with EXP-001: a generic summary prompt carries the rule through for Mistral almost every time and for `gpt-oss-20b` about half the time. Whether a rule survives compaction depends on the model that writes the summary.

### Not shown
One pack, one prompt, one free model at 27 seeds; the owner's hand audit of these summaries is still to come.

## Deviations log
| Date | What changed | Why |
|---|---|---|
