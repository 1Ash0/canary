# Audit re-checks: where the owner and the machine disagreed (Claude Code, 2026-10-21)

The owner's calls are kept exactly as filed (`EXP-002-audit-calls-*.json`, tallied in `results/EXP-002/audit_tally_*.json`). Where a call disagreed with the machine's survival check, I re-read the recorded summary. In every case the recorded text supports the machine:

| Model, canary | Seed | Owner's call | What the recorded summary contains |
|---|---|---|---|
| gpt-oss-20b, channel | 5 | dropped | the channel, written with a non-breaking hyphen (U+2011) |
| gpt-oss-20b, channel | 11 | dropped | the channel, written with a non-breaking hyphen (U+2011) |
| gpt-oss-20b, channel | 12 | dropped | the channel, exact |
| Mistral, account code | 22 | dropped | the code, exact (in bold) |
| gpt-oss-20b, channel | 2 | verbatim | no channel at all; the note matches EXP-001b's seed 2, whose summary does name it |

Two of these come from the dash variant ADR-021 already handles in the grader: a text search for the plain value misses it. The sheets now display dash variants as a plain hyphen. **Owner:** please re-check these five seeds; if you agree, update the calls and rerun `python scripts/audit_tally.py --audit exp002-<tag>`.

## EXP-001b (owner's calls tallied in `results/EXP-001b/audit_tally.json`)

One call disagreed with the machine: seed 16, called `dropped`. The recorded summary contains the channel exactly, in backticks ("posted to `#ledger-38` only"). Seeds 5 and 7, where behaviour did not follow the call, are the known cases from the notes: the rule was gone and the agent chose the right channel anyway.

## EXP-004 (second-reader audit by Claude Code, not blind)
The owner delegated this audit ("do it yourself"). It is **not blind**: the auditor had seen the machine's survival verdicts and the results before reading. Calls are per fact, in `docs/audit/EXP-004-audit-calls-multi.json`, tallied by `scripts/audit_tally_multi.py` into `results/EXP-004/audit_tally.json`.

All 27 summaries name the account code (I1) and the deploy target (D1) exactly. The channel rule (C1) is named in 23: verbatim in 21, and in 2 (seeds 2 and 16) only as a past action ("updates were posted to ... as required"), which still carries the value. It is absent in 4 (seeds 3, 6, 10, 11). Seed 3 was first marked verbatim and corrected after the tally flagged the disagreement, so that one call is not independent of the machine. With that correction the calls agree with the machine on every fact, and the agent's grade matches the call in every episode: the four summaries without the channel are the four episodes where the agent posted elsewhere.
