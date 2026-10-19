# EXP-NNN — short title

Status: DRAFT | PREREGISTERED (date, git sha) | RUN | ANALYSED
Epistemic tag for results: measured

## Question
(one sentence)

## Hypotheses (directional, written BEFORE running)
- H1:
- Why we expect it:

## Design
- Pack(s):
- Conditions: floor / control / length_matched / treatment(policy)
- Policies:
- Models (ids as the provider reports them):
- Seeds / scenarios:
- Trials per cell (n) and temperature:
- Compaction budget:
- Compaction prompt version:

## Comparisons
- Primary (max 3, chosen now):
  1.
- Exploratory (labelled as such):

## Analysis plan
- Intervals: Wilson per cell; bootstrap CI for risk differences
- Paired test: exact McNemar on same-seed pairs
- Multiple comparisons: BH for any non-primary family
- Stop rule: fixed n, no peeking

## Cost
- Planned calls, estimated tokens/cost (from dry-run, dated price table):
- Hard cap (--max-usd):

## What would change our mind / make us stop

## Interpretation rules (written in advance)
- Counts as "replicates":
- Counts as a null:

## Deviations log (fill in afterwards, honestly)
| Date | What changed | Why | Effect on interpretation |

## Results
(link to results/<exp_id>/..., never paste numbers by hand)

## Notebook entry
(link to docs/notebook/...)
