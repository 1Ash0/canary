# PROJECT — ctxcheck (working name)

## One line
A test kit and flight recorder for agent context-compaction policies: see what is in the window at every step, see what compaction dropped, and test whether the agent's behaviour changed.

Positioning (be careful with this sentence): "pytest for context policies" is the aspiration for the tool layer. It is only true once M6 ships. Until then say "a flight recorder and canary lab".

## The question
When a harness compacts its context (truncates, summarizes, masks, offloads, resets), what does the agent stop knowing, and does it act differently afterwards?

## Why this is worth building (honest version)
- Harness engineering is young and mostly unmeasured. One survey of 97 harnesses found 60% had neither tests nor evals (see PRIOR_ART).
- Compaction failures are silent: the agent keeps working coherently on a summary that lost something. The failure is *behavioural*, so it has to be tested behaviourally.
- Research exists (ConstraintRot, Slipstream, TRACE, ARC, ACON). What a practitioner still lacks, to the best of my search, is something they can point at their own compaction policy and watch. **That "to the best of my search" is an open verification task, not a fact.**

## This is not a novelty project
The research contribution is deliberately modest: replicate a published effect on our own harness, extend it with additional canary types, and report honestly, including nulls. The product contribution is the playground and the tool. The learning contribution (understanding harnesses, context mechanics, eval statistics) is the main goal for the builder.

## The three layers (every release must have all three, even if thin)
1. **Playground (30 seconds, zero install).** A public static site. Open a recorded run, scrub through steps, watch the context window fill by category, see the compaction event and what was lost, share a permalink to an exact step. Never requires an API key.
2. **Tool (real use).** A Python library and CLI. Bring your own compaction policy as a Python file, run canary scenarios against it with a model you choose, get a survival report. Exits non-zero in CI when a canary fails.
3. **Lab (the moat).** Preregistered experiments, deterministic grading, uncertainty bands, versioned results, cassettes so anyone can reproduce without paying.

## Users
- **Harness builder** choosing or tuning a compaction policy. Wants: "does mine forget constraints?"
- **Curious engineer** reading a post. Wants: to click a link and see something real in 30 seconds.
- **Researcher / contributor.** Wants: add a policy, canary pack or provider as one file.
- **The builder (Asmit).** Wants: depth. The project is the vehicle for learning.

## Scope for v0.1 (the fence)
In:
- Own mini harness (agent loop, tool dispatch, tracer), provider-agnostic, with record/replay cassettes and a budget guard.
- Trace schema v0 (JSONL events) and a token ledger.
- Four policies: `recency_truncate`, `head_tail`, `llm_summary`, `observation_mask`.
- Canary packs: `constraint` and `identifier`.
- Deterministic graders (grade by the tool call the agent emits, no LLM judge in primary metrics).
- Stats: Wilson intervals, bootstrap, exact McNemar for paired comparisons.
- Web: flight recorder, survival heatmap, lab notebook pages, static export.
- Experiments EXP-001 to EXP-003 (see EVAL_DESIGN).

Out (goes to ROADMAP Later with a trigger):
- Pinning, offload, reset+handoff policies (v0.2).
- Canary packs: failed_approach, decision_rationale, preference, execution_state, superseded_fact.
- Importing Claude Code / Codex session logs into the trace schema.
- MCP server wrapper of the tool, multi-agent, learned compaction, async validation (Slipstream-style).
- Accounts, hosting user logs, live-run-from-browser, leaderboards.

## Non-goals
Not a new compaction algorithm. Not a general observability platform. Not a benchmark leaderboard. Not an attempt to beat published systems. Not a framework for building agents.

## Success criteria (v0.1)
1. A public URL where a stranger opens a run and a permalink to a specific step in under 30 seconds.
2. One command reproduces the headline result from cassettes with no network and no API key.
3. A measured result with intervals: either the published Governance Decay direction replicates on at least two models we can access, or we report an honest null and what we learned.
4. Asmit can explain every core module without notes (gates in LEARNING.md all passed).
5. Three public posts at M1, M4, M5, each tagged with its epistemic status and linking to a step permalink.
6. A README a stranger can follow to add their own policy file.

## Conversation-readiness
Success is not "an engineer replies." It is that the artifact is specific enough to ask good questions. Before each post, write three precise questions the work raises (for example: "How do you evaluate that your summarizer keeps standing constraints?"). Questions go in the post only if they are genuine.

## Evolution
Direction may change as results and learning come in. The pivot protocol (ADR + doc updates + notebook entry) is how it changes safely. Interfaces (Policy, CanaryPack, Provider, Grader) and the trace schema are the stable seams; everything else may be rewritten.

## Extension points kept open (not built)
- Trace schema is vendor-neutral so other projects can write or read it.
- Policies, canary packs and providers are single-file plugins.
- A later MCP wrapper (`run_canaries`, `explain_loss`) is possible because the CLI is a thin layer over the library.
