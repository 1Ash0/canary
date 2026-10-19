# LEDGER — understanding gates passed

One row per gate. Fill it in after the explain-back conversation with Claude Code. The "one sentence" column is your words — it does not need to be perfectly technical, only honest.

A milestone row (M0, M1 …) records that the structural work is in place, not a learning gate.

| Gate | What | Date | One sentence in your words |
|---|---|---|---|
| M0 | Spine bootstrapped | 2026-10-19 | Repo layout, tooling, CI skeleton, and all M0 docs are in place; a fresh clone will pass `make check` offline once uv is installed and `uv sync --dev` has been run. |
| G0 | Tokens + context window | 2026-10-19 | A token is a BPE chunk ~3-4 chars of common text; the harness counts locally to decide when to compact before calling the API, to build length_matched, and to show dry-run cost estimates; doubling the system prompt eats directly into the remaining message budget because every call re-sends it from scratch. |
| G1 | JSONL trace + event sourcing | 2026-10-19 | Events store what happened, not computed state; all views are derived by replaying the file so adding a new view requires no migration; seq is a logical clock that survives clock skew where timestamps alone cannot order simultaneous events. |
| G2 | Canaries + conditions + deterministic grading | 2026-10-19 | A canary is a planted rule the agent must still act on after compaction, graded by parsing the emitted tool call not the text; floor measures baseline, control proves the scenario works, length_matched isolates size from content loss, treatment measures the policy. |
