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
(empty until the run)

## Deviations log
| Date | What changed | Why |
|---|---|---|
