# 2026-10-20 — Design direction: name, look, framework

*Drafted by Claude Code from the D0 answers; Asmit to review and edit into his own words.*

**Context.** I started the design subsystem handoff (`docs/design/HANDOFF.md`). D0 found that the live landing page (dark, yellow, dither hero) contradicted DESIGN.md, and that the brief's "warm engineering notebook" identity had no concrete values.

**What I decided at D0**
- Public name **Canary**; the package/CLI stays `ctxcheck` because `canary` is taken on PyPI (ADR-013).
- Look: "premium, like GSAP". This deliberately moves away from the notebook-only brief. Recorded as a pivot. ADR-014 follows once the resources have been read first-hand.
- Framework and references delegated to Claude, to be decided with evidence in D1.
- I dropped the Creation-of-Adam dither experiment (uncommitted edit discarded; the committed versions stay in git history).

**What failed.** Three rounds on the dither hero produced a pixel smear, not hands. Lesson: a decorative hero with no data behind it ate a session and still looked generic. The strata view should carry the hero instead.

**Open questions.** Can "premium" coexist with the honesty rules (synthetic label, traceable numbers, vermilion only for loss)? D2 renders candidates to find out.
