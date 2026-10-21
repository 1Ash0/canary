# EXP-002 audit: re-check of disagreements (Claude Code, 2026-10-21)

The owner's calls are kept exactly as filed (`EXP-002-audit-calls-*.json`, tallied in `results/EXP-002/audit_tally_*.json`). Where a call disagreed with the machine's survival check, I re-read the recorded summary. In every case the recorded text supports the machine:

| Model, canary | Seed | Owner's call | What the recorded summary contains |
|---|---|---|---|
| gpt-oss-20b, channel | 5 | dropped | the channel, written with a non-breaking hyphen (U+2011) |
| gpt-oss-20b, channel | 11 | dropped | the channel, written with a non-breaking hyphen (U+2011) |
| gpt-oss-20b, channel | 12 | dropped | the channel, exact |
| Mistral, account code | 22 | dropped | the code, exact (in bold) |
| gpt-oss-20b, channel | 2 | verbatim | no channel at all; the note matches EXP-001b's seed 2, whose summary does name it |

Two of these come from the dash variant ADR-021 already handles in the grader: a text search for the plain value misses it. The sheets now display dash variants as a plain hyphen. **Owner:** please re-check these five seeds; if you agree, update the calls and rerun `python scripts/audit_tally.py --audit exp002-<tag>`.
