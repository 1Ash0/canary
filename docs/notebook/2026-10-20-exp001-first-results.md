# 2026-10-20 — EXP-001 first results: not replicated at pilot scale, and what the instrument taught us

*Drafted by Claude Code from the committed data. The numbers live in `docs/experiments/EXP-001.md` (Results) and are checked against `results/EXP-001/summary.json` by `scripts/check_claims.py`; this entry deliberately repeats few of them. The manual audit of summaries is still the owner's.*

## What was run
EXP-001 (frozen before running) on three free models, 10 seeds each, four conditions per seed: Groq `openai/gpt-oss-120b`, Mistral `ministral-14b-latest`, Gemini `gemini-3.1-flash-lite`. The second model changed twice after the freeze, both logged: OpenRouter's model was dropped because of its daily cap, then Gemini turned out not to summarise.

## What the data say
- The pack works: for every model, floor behaves like chance (the model cannot know the channel) and control never breaks the rule.
- **Replication: no, at this scale.** Neither model that actually summarises reaches the preregistered bar. Groq is directional only; Mistral is inconclusive because its summaries almost always carried the rule through.
- Behaviour followed what the summary kept almost one for one (exploratory). The experiment's real finding so far is that the summarizing model, under a generic prompt, decides whether the rule survives. That is a statement about this pilot, not about the models.

## What went wrong, kept on the record
1. **Gemini's "summaries" were echoes of the transcript.** Found in the audit, not by the preregistered checks, because the preregistration had no test that a summary is a summary. That is a gap in my preregistration. The data are kept and flagged; the check was added afterwards and says so.
2. **The 400-token summary cap in the design was never applied** (the adapters ignored a per-call cap), so Groq's summaries ran under 1024 tokens including reasoning. Fixed later; Mistral's run had the real cap, so the two are not like for like.
3. **Cell keys ignored the model**, so the first Gemini run silently did nothing. Nothing was overwritten, but I should have had a two-model test before the first live call. Fixed with a test.
4. **A provider rejection on the summary call aborted the run** until I decided, after seeing it, that it is an outcome to record (`not_applicable`). Logged as a deviation, decided before looking at any rate.
5. **Preregistered rules were tightened twice by what I saw while running** (exact test alongside the bootstrap; validity flag). Each is logged with when and why. Anyone reading should weigh results from rules written after seeing data less than rules written before.

## What this does not show
Nothing here says compaction does or does not erase constraints in general. It is one prompt, one pack, 10 seeds, two usable models, free-tier models that change. A prompt that tells the summarizer to keep rules (v2) is untested.

## Next, in order of how much each changes the picture
1. The owner's manual audit of at least 20 summaries (the cassettes hold them): are rules reworded rather than kept verbatim? Verbatim survival undercounts those.
2. Reaching 27 seeds on the two usable models. Free-tier daily limits make that several days; `ctxcheck run` resumes.
3. EXP-002 (policy comparison) only needs one usable summarizing model and is cheap for the deterministic policies; its drafts are in `docs/experiments/`.
4. Prompt v2 as a sensitivity check (preregistered as exploratory).
