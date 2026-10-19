# DECISIONS (ADRs, append-only)

Format: **ADR-NNN — Title** · Status (Proposed/Accepted/Superseded) · Context · Decision · Consequences · Revisit when.
Never edit an accepted ADR to change history; add a new ADR that supersedes it.

---

### ADR-001 — Replicate, extend, productize (not novelty)
Status: Accepted. Context: PRIOR_ART shows compaction and constraint decay are already studied (ConstraintRot, Slipstream, TRACE, ARC, ACON). Decision: the research contribution is a replication on our own harness plus extension; the main deliverables are the playground and tool, and the builder's depth. Consequences: we credit prior work prominently; a null result is acceptable; claims stay modest. Revisit when: PRIOR_ART open tasks reveal an equivalent tool, or EXP-001 is a clean null.

### ADR-002 — Behavioural grading with deterministic parsing
Status: Accepted. Decision: primary grades come from parsing the emitted tool call; no LLM judge in headline numbers. Consequences: cheaper, reproducible, auditable; limits us to canaries that cause a checkable action. Judge-based survival checks are secondary and labelled. Revisit when: a canary type needs semantic grading (e.g. paraphrased rationale).

### ADR-003 — Python core, static web front end
Status: Accepted. Decision: Python 3.12 for harness, experiments and stats (you already know it, ecosystem fits); Next.js static export for the web. The web app reads files only; it never calls a model. Consequences: the playground lasts indefinitely and needs no hosting beyond static files. Revisit when: a live-run feature is wanted (it is explicitly out of scope).

### ADR-004 — Pydantic as single source of truth for schemas
Status: Accepted. Decision: pydantic v2 models → JSON Schema → generated TypeScript types. A CI drift check fails on mismatch. Consequences: no hand-maintained duplicate schemas. Revisit when: generation becomes painful.

### ADR-005 — Cassettes for reproducibility
Status: Accepted. Decision: all model calls go through a cassette layer; CI is replay-only; the key includes `trial_index`. Consequences: free reproduction, deterministic tests; cassettes can go stale and must carry version metadata. Revisit when: cassette size becomes a problem (then consider compression or external storage).

### ADR-006 — Own mini harness instead of wrapping an existing framework
Status: Accepted. Decision: write a small harness (loop, tools, tracer) ourselves for v0.1. Consequences: the builder learns the internals; full control over trace events and policy hooks; we do not claim parity with production harnesses. Real-harness adapters are Later. Revisit when: M6 and adapter trigger.

### ADR-007 — Soft constraints as the default canary design
Status: Accepted. Context: ConstraintRot found decay concentrates on arbitrary, deployment-specific rules, while hard safety norms are masked by alignment training. Decision: canaries default to soft rules and seeded random values. Consequences: results are more sensitive and less contaminated; external validity limits must be stated.

### ADR-008 — Recorded vs simulated is always labelled
Status: Accepted. Decision: any UI element or figure that shows a deterministic policy re-applied to a recorded run is labelled `simulated`; LLM-based outcomes appear only from recordings. Consequences: slightly less flexible UI; honest provenance.

### ADR-009 — Working name `ctxcheck`
Status: Accepted (name check done, Oct 2026). Decision: keep `ctxcheck` as the working name. Verification: GitHub search found no standalone repo named `ctxcheck`; one project (YourBIMpossible/claude-tools) uses the string in a description as an internal tool name, not as a published package or top-level repo name. PyPI check was CAPTCHA-blocked — direct check via `pip index versions ctxcheck` or `pip install ctxcheck --dry-run` is required before the first publish (M1 exit criterion). Consequences: rename before first publish only if PyPI check fails. Revisit when: M1 publish step.

### ADR-010 — Core vs plumbing learning lanes
Status: Accepted. Decision: Teach-First gates apply to all of `src/ctxcheck/`; CI/config/CSS use a lightweight lane (5-line explanation, no gate). Consequences: keeps depth where it matters without blocking on tooling. Revisit when: the builder wants everything deep.

### ADR-011 — Scope fence and pivot protocol
Status: Accepted. Decision: out-of-scope ideas go to ROADMAP Later with triggers; direction changes require an ADR before code. Consequences: slower to chase ideas, much harder to drift. Revisit when: never lightly.

### ADR-012 — Budget guard and dry-run before any live call
Status: Accepted. Decision: no live model call without `--max-usd` and a preceding dry-run estimate from a user-supplied dated price table. Consequences: prevents surprise spend; prices are never hard-coded.

---
(Append new ADRs below.)
