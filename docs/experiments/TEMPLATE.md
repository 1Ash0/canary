# EXP-NNN — title

Status: draft | frozen (commit hash: ______) | run | reported
Epistemic tag of results: measured | simulated (never both)

## Question
One sentence.

## Hypotheses (directional, stated before running)
- H1: ... because ...
- What I expect and why, then see.

## Design
- Pack(s), conditions, policies (with options and prompt version), models (ids as the provider lists them), seeds, trials, temperature (or "provider default"), budgets (window limit, request/token caps, daily limits).
- Planned n per cell, and the n actually reachable under the caps (ADR-018). State both.

## Primary comparisons (at most three, chosen before looking)
1. ...

## Exploratory (labelled as such in any report)
- ...

## Analysis plan
Wilson intervals per cell; exact McNemar and paired bootstrap risk difference for paired comparisons; Benjamini-Hochberg across the primary comparisons. `not_applicable` handling.

## Cost and caps
Command, dry-run output, caps.

## Validity checks (what would make the result uninterpretable)
- floor ...; control ...; not_applicable share ...

## Interpretation rules (written in advance)
- Replicates if ...; null if ...; inconclusive if ...

## What would change our mind / what would make us stop
- ...

## Manual audit
Which summaries are read by hand, how many, what is recorded.

## Results
(empty until real episodes exist)

## Deviations log (filled in afterwards, honestly)
| Date | What changed | Why |
|---|---|---|
