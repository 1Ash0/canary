# Notebook entry: first-session verification (Step 2)
Date: 2026-10-19  
Epistemic tag: **reasoned + web searches** (no local model runs)

## What this covers
All 8 open verification tasks from docs/PRIOR_ART.md, done in the first session.

---

## Task 1 — ConstraintRot released code, licence

**Finding:** No public GitHub repository for ConstraintRot scenarios, grader, or evaluation code found as of Oct 2026. Multiple searches (GitHub, arXiv project pages, related-paper links) returned nothing. The paper (arXiv 2606.22528, Chen et al., "Governance Decay: How Context Compaction Silently Erases Safety Constraints in Long-Horizon LLM Agents") exists and is readable as HTML v2.

**Consequence:** scenarios and the deterministic grader must be reimplemented from the paper text. The benchmark design (9 tasks × 3 reps = 27 per cell, single-tool-call grade, floor/control/compaction conditions) is described clearly enough to reimplement.

**Licence:** not determinable without a released repo. If/when a repo appears, check before vendoring scenarios with attribution.

**Numbers corrected:** PRIOR_ART previously said "30% pooled"; the HTML v2 body reads "37% pooled". The abstract may cite a different figure (up to 59% is mentioned, possibly a per-condition peak). Neither has been verified from the PDF. Both figures should be cited as `[unverified exact value, verify from PDF]` until we have the full paper.

---

## Task 2 — Supplementary material / compaction prompts / budget definition

**Finding:** The supplementary material is not freely accessible online as of this search. Key numbers from the HTML v2 body:
- recency-truncate: 38% violation
- hierarchical: 36% violation  
- LLM summarize: 26% violation
- head_tail: 0% violation
- Constraint Pinning (defense): ~0% under all strategies
- n=27 per cell; 9 tasks × 3 reps = 1,323 total episodes

**Consequence:** compaction prompt wording and "summary budget" definition remain unknown until the PDF/supplementary is accessed. This matters for faithful replication — our `llm_summary` policy's compaction prompt will be our own design, not a copy of theirs.

---

## Task 3 — Existing session viewers and CI-style compaction testing tools

**Found:** `github.com/manavgup/context-analyzer`
- Architecture: Claude Code PreCompact/PostCompact hooks → SQLite → FastAPI REST → React dashboard
- What it shows: token breakdown per conversation step, tool calls, hook events, subagent summaries, before/after compaction token counts
- What it does NOT do: run scripted canary scenarios, run a policy matrix, produce pass/fail results, output a results JSON with intervals, support CI integration

**Comparison:**

| | context-analyzer | ctxcheck (planned) |
|---|---|---|
| Token breakdown per step | yes | yes (context strata view) |
| Canary survival testing | no | yes (core feature) |
| Policy × model matrix | no | yes |
| Deterministic grading | no | yes |
| CI integration | no | yes |
| Survival intervals | no | yes |
| Playground (no install) | no | yes |
| Retrospective on real sessions | yes | later |

**Conclusion:** context-analyzer is a session inspector. ctxcheck is a testing tool. They are in different categories. No equivalent CI testing tool found.

Also noted: `YourBIMpossible/claude-tools` uses "ctxcheck" in its repo description as an internal tool name in a toolbelt, not as a standalone package. Not a conflict.

---

## Task 4 — Anthropic primary posts on context engineering

All five posts confirmed. Key facts relevant to ctxcheck design:

1. **Compaction** = summarise a near-full context and start a fresh window. Preserves: decisions, open bugs, implementation details. Discards: redundant tool outputs, repetitive exchanges.
2. **"Art of compaction"**: "Start by maximising recall … then iterate to improve precision by eliminating superfluous content."
3. **Tool result clearing** = lighter form: replace tool output content only, not history. Distinct from full compaction.
4. **Context resets** = discard and restart; mentioned as a pattern but not the primary approach.
5. **Prompt cache invalidation**: "The cache follows the hierarchy: tools → system → messages. Changes at each level invalidate that level and all subsequent levels." Editing any message at or before the cache breakpoint invalidates from that point. Compaction always invalidates the message-level cache (new context ≠ old hash).
6. All five posts confirmed at anthropic.com/engineering/…; exact URLs in PRIOR_ART.md.

**PRIOR_ART status updated** from [unverified] to [read].

---

## Task 5 — TRACE and ARC: do they change our policy or canary list?

**TRACE** (arXiv 2608.06503, Min et al., Aug 2026, "Toward Reliable Context Compression for Long-Horizon Agents: An Empirical Study of Execution Instability"):
- Studies execution-state mislocalization: after compression, agent re-executes completed steps or skips pending ones.
- **Decision:** `execution_state` canary type in EVAL_DESIGN is well-motivated by TRACE. Stays in "Later" for v0.1 (out of scope; confirmed). No change to current policy or canary list.

**ARC** (arXiv 2607.25066, Dang et al., "Addressable Recall Compaction for Long Context-Window Control in AI Agents"):
- Lossless compaction via archival storage + addressable recall. Archives content with ids; retrieves on demand.
- Fundamentally different from what ctxcheck tests. ARC prevents loss; ctxcheck measures it.
- `observation_mask` in our policies is conceptually adjacent (replace with tag) but simpler and has no retrieval.
- **Decision:** no change to v0.1 policy or canary list. `addressable recall` canary (tests whether a harness's recall mechanism works correctly) is a valid v1 extension idea; moved to ROADMAP Later by ADR-011.

---

## Task 6 — Name availability: `ctxcheck`

- **GitHub:** no standalone repo named `ctxcheck` found. YourBIMpossible/claude-tools uses the string in a description as an internal tool, not a top-level repo name.
- **PyPI:** direct check blocked by Cloudflare CAPTCHA. Unconfirmed. **Action required before M1:** run `pip index versions ctxcheck` or `pip install ctxcheck --dry-run` to verify availability. If taken, rename before first publish.
- **Decision:** keep name provisionally. ADR-009 updated to Accepted with caveat.

---

## Task 7 — Factory.ai primary source

**Found and read:** factory.com/news/evaluating-compression (December 16, 2025)

**Actual finding:** quality scores (0–5 scale, probe-based LLM judge) for three compression approaches:
- Factory Dragonfly: 3.70/5.0
- Anthropic Claude summarisation: 3.44/5.0  
- OpenAI summarisation: 3.35/5.0

Artefact trail sub-task scored lowest across all methods (~2.45/5.0 for best method).

**The "37% multi-session retention" figure is NOT in this source.** It appeared in morphllm.com's summary table labelled "Multi-Session Retention: 37%" — appears to be morphllm's own framing/calculation, not Factory's reported metric. This figure has been removed from PRIOR_ART.md.

**Correction applied:** PRIOR_ART Factory.ai row updated from [second-hand] to [read] with corrected finding.

---

## Task 8 — Provider facts from primary docs

**Prompt caching (Anthropic):**
- Cache is keyed by a hash of the prefix up to the `cache_control` breakpoint
- "Because the hash is cumulative, covering everything up to and including the breakpoint, changing any block at or before the breakpoint produces a different hash on the next request"
- Hierarchy: tools → system → messages. Editing a tool definition invalidates the entire cache; editing an earlier message invalidates from that message forward.
- **Implication for compaction:** any compaction event that rewrites message history invalidates the message-level cache. Every compaction starts a fresh cache. Tool result clearing without history rewrite may partially preserve the cache.
- **JSON key ordering:** Anthropic docs explicitly warn that random key ordering (e.g. some JSON serializers) breaks caches. Our cassette canonical-JSON spec (`sort_keys=True`) is correct for the same reason.
- TTL: 5 minutes default, 1 hour available.

**Tool-use / tool-result pairing:**
- The Anthropic API requires that a `tool_use` block in an assistant turn be followed by a `tool_result` block in the next user turn. Orphaned tool calls produce an API validation error.
- **Implication for policies:** ARCHITECTURE.md Policy invariant 2 ("Tool pairing: a tool_call is never kept without its tool_result, and vice versa") is confirmed necessary. This is a real compaction bug: dropping a tool_call without its result or vice versa will cause the next API request to fail.
- **Source:** Anthropic tool use documentation (anthropic.com/docs/tool-use); confirmed from ARCHITECTURE.md invariant text.

---

## Summary of corrections to docs

| Doc | Change |
|---|---|
| PRIOR_ART.md | ConstraintRot: "30% pooled" → "37% pooled" + [unverified exact value]; no public code note; supplementary not accessed |
| PRIOR_ART.md | Factory.ai: [second-hand] → [read]; "37% retention" removed; replaced with actual quality scores |
| PRIOR_ART.md | Anthropic posts: [unverified] → [read]; key compaction behaviours recorded |
| PRIOR_ART.md | TRACE: added full title + arXiv id; confirmed execution-state relevance |
| PRIOR_ART.md | ARC: added arXiv id; confirmed it doesn't change v0.1 scope |
| DECISIONS.md | ADR-009: Proposed → Accepted with PyPI caveat |
| ARCHITECTURE.md | Cassette key: added canonical JSON spec (sort_keys=True) |
| EVAL_DESIGN.md | length_matched: corrected definition (post-compaction token count) |
| EVAL_DESIGN.md | soft-only bias scope note added |

## No-change decisions

- `execution_state` canary: stays in Later
- `addressable recall` canary: stays out of v0.1, added to ROADMAP Later idea
- Canary default (soft/arbitrary rules): confirmed by ConstraintRot soft vs hard finding
- Cassette canonical JSON: confirmed correct by Anthropic caching docs warning
