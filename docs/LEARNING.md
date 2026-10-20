# LEARNING — ctxcheck

## How this works

Two Claude instances help you. They have different jobs:

- **Claude Chat** is your tutor. It explains concepts, answers questions, reads papers with you. It does not touch code.
- **Claude Code (this session)** is your builder. It writes code, runs things, and tells you when to go to Chat.

The pattern for every unit:

1. I (Code) explain the concept in plain English — why it matters for *this* project specifically.
2. I give you an exact prompt to paste into Chat. Chat will teach you the concept properly.
3. Sometimes I tell you to read a specific article or paper with Chat (I give you focus questions).
4. We build something together — a small, working Python file.
5. You explain it back to me in your own words. That's the gate. I won't move on until you've got it.

You control the pace. If something is unclear, go back to Chat. The goal is that by M6 you can explain every decision in this codebase to a peer.

---

## The project, in plain English

Imagine a coding assistant working on a long task. You told it early on: "always put your status updates in #ops-7." Hours pass. The assistant has seen thousands of messages. Its context window — the text it can hold in memory at once — is almost full.

The harness (the code running the agent) has to do something. It "compacts" the context: either throwing away the oldest messages, asking another AI to write a summary, or some combination. After compaction, the agent's memory is shorter. But the summary forgot to mention #ops-7. Now it sends the next update to the wrong channel.

**ctxcheck measures how often this happens.** It:
1. Plants a "canary" — a rule or fact — early in a scripted conversation.
2. Fills the context with boring filler turns.
3. Applies a compaction strategy.
4. Asks the agent a question that requires acting on the canary.
5. Grades the answer: did it follow the rule?
6. Does this many times, across multiple strategies and models, and reports survival rates with statistical intervals.

The project has three deliverables:
- **Lab** — the Python harness that runs tests and writes `results/`.
- **Playground** — a website that shows the results visually.
- **Tool** — a CLI other developers can use on their own agents.

You're building all three, learning each piece as you go.

---

## Concept map

One sentence each. You will understand all of these by the end.

| ID | Concept | One sentence |
|---|---|---|
| C01 | Tokens | LLMs don't count characters or words — they count "tokens", which are roughly 3-4 characters of common text |
| C02 | Context window | The maximum tokens a model can hold per request — exact size is per-model config, not a project constant |
| C03 | Local vs provider count | tiktoken gives a local *estimate*; the provider reports the authoritative count split across three usage fields |
| C04 | Prompt caching | The provider can skip re-processing a prefix it already computed, if the prefix hasn't changed |
| C05 | JSONL trace | Every event in a run (message sent, tool called, canary planted, compaction applied) written one-per-line as JSON |
| C06 | Event sourcing | The JSONL file is the source of truth; every view (token chart, survival table) is computed from it |
| C07 | Canary | A planted fact or rule that the agent must still act on after compaction |
| C08 | Conditions | floor (no canary), control (canary, no compaction), length_matched (canary, same token count, no compaction), treatment (canary + compaction) |
| C09 | Deterministic grading | Grade the agent by parsing the tool call it emits — no LLM judge, no text matching |
| C10 | Cassette | A recorded API request+response stored on disk so tests can replay it without spending money |
| C11 | Cassette key | A hash of the exact request — ensures a replay is playing back the right thing |
| C12 | Compaction policy | The algorithm that decides what to keep and what to drop (recency-truncate, head-tail, LLM summarize, observation-mask) |
| C13 | Tool pairing invariant | A tool call and its result must always be kept or dropped together — providers reject orphans |
| C14 | Wilson score interval | A confidence interval for a proportion (k successes in n trials) that works for small n and extreme rates |
| C15 | McNemar's test | A statistical test for comparing two conditions on the *same* set of trials (paired design) |
| C16 | Paired design | Running the same seeds under two conditions so you can compare them without needing huge sample sizes |

---

## Units

### U0 — Tokens and counting

**What you'll understand:** What a token is, why every limit in this project is measured in tokens, and why your local count will never exactly match what the provider bills you.

**Why this comes first:** Almost nothing else in ctxcheck makes sense without it. The context window is in tokens. The compaction budget is in tokens. The length-matched condition is in tokens. If you don't know what you're counting, you can't reason about any of the results.

---

**Step 1 — Go to Claude Chat now.**

Paste this:

> I'm building a Python testing tool for AI agent context compaction. I need to understand tokens from first principles. Please explain:
> 1. What is a token in the context of a language model? How does it differ from a character or a word?
> 2. Why do models have a context window measured in tokens instead of characters?
> 3. I'll be using `tiktoken` as a proxy tokenizer to count tokens locally before making API calls. tiktoken is OpenAI's tokenizer, not Anthropic's — why might my local estimate differ from what the Anthropic API actually bills me? (There's also a `count_tokens` endpoint — when would I use that instead?)
> 4. What does it mean when people say "4k tokens" or "200k tokens"? Give me a concrete sense of scale.
> Keep your explanation simple — I'm a second-year CS student who knows Python but is new to LLM APIs.

Read and discuss with Chat until you feel solid on these four questions.

---

**Step 2 — Read this together with Chat (optional but recommended for C04).**

We verified from Anthropic's caching docs that the prompt cache is keyed on a prefix hash, and editing any message in the prefix invalidates from that point forward. In U1 you'll see why this matters for compaction. You don't need to read the docs now, but you can ask Chat:

> Explain prompt caching in the Anthropic API. A "cache breakpoint" marks the end of the cached prefix. What happens to the cache when the conversation changes? Why does this mean every compaction event starts a fresh cache?

Note verified in Chat (Oct 2026): `usage` has three input fields — `input_tokens`, `cache_read_input_tokens`, `cache_creation_input_tokens`. Cache hits depend on TTL (5 min default, 1 h costs extra). These fields are **recorded, not simulated** — cassettes store what the API actually returned; test replays cannot fake cache behaviour.

---

**Step 3 — Build `learn/tokens.py`.**

I will write this with you. It will:
- Load a tokenizer (tiktoken, `cl100k_base` encoding)
- Count the tokens in a string
- Print a "token ledger" for a short conversation: each message with its role, text, and token count, plus a running total and a "remaining budget" line

This is the first file we build together. It's small, runnable, and you'll use it as a mental model for everything that follows.

The ledger will have two count columns: `local_estimate` (tiktoken) and `provider_reported` (empty until a live run; equals `input_tokens + cache_read_input_tokens + cache_creation_input_tokens` from the usage object). The gap between them is what we'll eventually measure with `count_tokens`.

Cache-hit fields (`cache_read_input_tokens`) are timing-dependent — they only appear in a real API response, not in a replay. In cassettes, they are recorded as observed; they are never simulated. The ledger must label this clearly.

**Gate G0 — before we build U1, explain back to me:**
1. In your own words, what is a token, and roughly how many tokens is a typical sentence?
2. Why does the harness count tokens locally before making an API call?
3. If you doubled the length of the system prompt, what happens to the remaining budget for the conversation?

---

### U1 — The trace (JSONL event log)

**What you'll understand:** Why every event in a run is written to a file one line at a time, and why every chart and table in the playground is computed from that file rather than stored separately.

**Why this matters:** The JSONL trace is the source of truth for everything in ctxcheck. If you don't understand why it's designed this way, you won't know what you're building toward when you write `schema/events.py`.

---

**Step 1 — Go to Claude Chat.**

Paste this:

> I'm designing a system where every event in an AI agent run gets written to a file, one JSON object per line (JSONL format). The events include: message sent, tool called, compaction applied, canary planted, canary graded. All views — a token chart, a list of what was dropped during compaction, a pass/fail result — are computed by reading the file back, not stored separately.
>
> Explain to me:
> 1. What is "event sourcing" or "log as truth"? Why is it a common pattern in distributed systems?
> 2. What are the advantages of this design for my project? (Think: what happens if I want to add a new view later? What happens if a run crashes halfway through?)
> 3. What would go wrong if instead I stored all the views directly (e.g., a token count per step stored as a field on each message object)?
>
> I'm a second-year CS student. Give me concrete examples, not abstract theory.

---

**Step 2 — Build `learn/trace.py`.**

We'll write a mini version of the trace: a function that appends events to a JSONL file, and another that reads them back. We'll simulate a tiny run: one `run_start` event, two `message` events, one `compaction` event, one `run_end` event. Then we'll derive a "token ledger" by replaying the file.

**Gate G1 — before U2:**
1. What is the difference between "storing data" and "storing events"? Why does ctxcheck store events?
2. If you wanted to add a new metric — say, "how many tool calls happened before the compaction event" — what would you do with the JSONL approach? What would you have to do if you'd stored aggregates instead?
3. What does `seq` (the monotonic counter on each event) give you that a timestamp doesn't?

---

### U1b — The trace schema in real code (M1)

**What you'll understand:** How the documented trace schema becomes pydantic v2 models in `src/ctxcheck/schema/events.py`, how one JSONL line is parsed into the right event class, and which facts belong in events versus views derived from them.

**Why now:** M1 needs a real trace. The recorder, the token ledger, the site and the video all read events, so this file is the seam everything else depends on (ARCHITECTURE: "small stable seams"). U1 taught the idea with `learn/trace.py`; this unit makes it the real, typed thing.

**Decisions to make first** (Claude Code recommends; you decide):
1. **Step:** store an explicit `step` (turn number) on events that belong to a turn, rather than deriving it from the nth model call. A synthetic fixture session has no model calls.
2. **Window limit:** `limit_tokens` on `run_start` (a run parameter).
3. **Tools layer:** `tools_tokens_est` on `run_start` (tool specs are fixed for a run).
4. **Canary fate (kept/changed/gone):** *derive* it by replaying `canary_planted` + `compaction` + the summary text (verbatim check). Do not store it, unless a judge model is added later (a judge's verdict is an observation, so it would be an event).
5. **Pairing ids** for control vs treatment: defer to M4 (an additive change later; scope fence).

**Step 1 — Go to Claude Chat.** Paste this:

> I'm turning a documented event schema into Python pydantic v2 models. It's a JSONL trace of an AI agent run with these event types: run_start, message, model_call, tool_call, tool_result, compaction, canary_planted, canary_probe, run_end. Every event has schema_version, run_id, seq (a monotonic counter), ts and a `type` field. Teach me, with small code examples:
> 1. What pydantic v2's BaseModel does: validation, `model_validate_json`, `model_dump_json`. What happens when a field has the wrong type?
> 2. Discriminated unions: each event class has `type: Literal["message"]` (etc.). How does `Annotated[Union[...], Field(discriminator="type")]` let pydantic pick the right class when it reads one JSONL line? Why is that better than trying each class in turn? What happens with an unknown `type`?
> 3. Schema versioning: events carry `schema_version: "0.1"`. What is an additive (minor) change versus a breaking (major) change? Give examples: adding an optional field, renaming a field, changing a field's type.
> 4. Event sourcing: I can either store a planted fact's "fate" (kept / changed / gone after compaction) as its own event, or compute it later by replaying the compaction event and the summary text. How do I decide whether something should be an event or a derived view?
> 5. `model_json_schema()` exports JSON Schema. How does that let a TypeScript web app share the same types without hand-writing them twice?
> I'm a second-year CS student who knows Python and has already learned the "log as source of truth" idea.

**Step 2 — Build `src/ctxcheck/schema/events.py` together.**
- All v0 event types from ARCHITECTURE, plus the fields from the decisions above.
- A `parse_event(line) -> TraceEvent` using the discriminated union.
- Two-sided tests in `tests/unit/`: valid lines parse to the right class; unknown types, missing fields and wrong types are rejected.

**Gate G1b — before the token ledger:**
1. How does pydantic know which class a JSONL line is? What happens to a line with `"type": "teleport"`?
2. Why is canary fate derived rather than stored, and what would change that?
3. Adding an optional `pair_id` later: minor or major version bump? Renaming `tokens_est`: which, and what else must ship with it?

---

### U2 — Canaries and grading

**What you'll understand:** What a canary is, why we grade behaviour (tool calls emitted) instead of text (does the summary mention the rule), and what the four conditions mean.

**Why this matters:** This is the core measurement unit of the project. If you don't understand the conditions, you can't interpret any result. If you don't understand why we grade tool calls and not text, you'll build the wrong thing.

---

**Step 1 — Read with Chat.**

This is the first time to open a paper with Chat. Paste this into Chat:

> I want to understand the core findings of a paper called "Governance Decay: How Context Compaction Silently Erases Safety Constraints in Long-Horizon LLM Agents" (arXiv 2606.22528). I don't have the full paper, so explain based on what you know or from the abstract:
>
> 1. What is ConstraintRot? What did the researchers plant in the conversation, and how did they grade whether the agent failed?
> 2. Why did they use a tool call as the grade signal, rather than asking "does the summary mention the rule?"
> 3. What were the four conditions they compared? Why do you need all four — why isn't just "compaction vs no compaction" enough?
> 4. What was the main finding about soft rules vs hard safety norms?
>
> I'm building a similar testing tool and want to understand the design choices.

---

**Step 2 — Go to Chat for the conditions specifically.**

Paste this separately (it's important enough to get right):

> I'm designing an experiment to measure whether context compaction causes an AI agent to violate a rule it was given. I have four conditions:
> - floor: the rule is never given; we test the agent's baseline behaviour
> - control: the rule is given; context is NOT compacted; we test whether the agent follows the rule normally
> - length_matched: the rule is given; context is NOT compacted; BUT we trim the filler turns so the total context is the same size as after compaction
> - treatment: the rule is given; context IS compacted; we test whether the agent still follows the rule
>
> Explain to me:
> 1. Why do I need the `floor` condition?
> 2. Why do I need `length_matched`? What specifically does it separate from `treatment`?
> 3. If `treatment` shows 40% violation and `control` shows 2%, what can I claim? What can I NOT claim without `length_matched`?

---

**Step 3 — Build `learn/grader.py`.**

A function that takes a tool call dict and a canary spec and returns `violated` or `respected`. Two-sided: fixtures that must fire, fixtures that must not.

**Gate G2 — before U3:**
1. What is a canary? Explain with a concrete example that isn't the one in the docs.
2. Why does ctxcheck grade tool calls instead of asking "does the summary mention the rule?"
3. In one sentence each: what does floor / control / length_matched / treatment each isolate?

---

### U3 — Cassettes

**What you'll understand:** What a cassette is, why the cassette key includes `trial_index`, and what "replay-only in CI" means.

**Why this matters:** Every experiment in ctxcheck is reproducible — if you ran it once, anyone can re-run it without calling an API. The cassette layer is what makes this possible. It's also what keeps `make check` free and fast.

---

**Step 1 — Go to Chat.**

Paste this:

> I'm building a record/replay layer for API calls. When recording, I call the real API and save the response to a JSON file. When replaying, I serve the saved response instead of calling the API. This is sometimes called the "VCR pattern" or "cassette testing."
>
> 1. Explain this pattern and why it's useful for reproducibility and cost.
> 2. I key each cassette by a hash of the exact request (model, messages, tools, temperature, and a `trial_index`). Why is `trial_index` in the key? (Hint: at temperature > 0, different trials should give different outputs.)
> 3. What goes wrong if I run 3 trials but all three replay the same cassette? Why is the variance I'd measure fake?
> 4. In CI, if a cassette is missing (the test needs an API call we've never recorded), the test should fail — not silently call the API. Why?

---

**Step 2 — Build `learn/cassette.py`.**

A minimal cassette: `record(key, fn)` calls `fn()` and writes to disk; `replay(key)` reads from disk; `auto(key, fn)` is record if missing, replay if present. Show that two calls with different `trial_index` save separate files.

**Gate G3 — before U4:**
1. What is a cassette and why do we use one?
2. Why does the cassette key include `trial_index`?
3. What would happen to your variance estimate if 5 trials all replayed the same cassette?

---

### U4 — Compaction policies

**What you'll understand:** What each policy does mechanically, what the tool-pairing invariant is and why it matters, and how to implement the simplest policy (`recency_truncate`).

**Why this matters:** The policies are the things being compared. You can't evaluate them if you don't understand what they actually do.

---

**Step 1 — Go to Chat.**

Paste this:

> I'm implementing four context compaction policies for an AI agent harness. Explain each one concretely — what messages are kept, what are dropped:
>
> 1. **recency_truncate**: drop the oldest messages until under budget
> 2. **head_tail**: keep the first N tokens and the last M tokens, drop the middle
> 3. **llm_summarize**: ask a model to write a summary of the dropped section, insert the summary as a special message
> 4. **observation_mask**: replace tool results (observations) with a placeholder tag, keeping the tool calls
>
> Then explain:
> 5. Why does dropping a tool call without also dropping its result (or vice versa) cause the API to reject the next request? What error would you see?
> 6. The ConstraintRot paper found recency_truncate was worst (38% violation) and head_tail was best (0%). What does that pattern suggest about *where* canaries are planted and where they survive?

---

**Step 2 — Build `learn/policy_recency.py`.**

The recency-truncate policy as a pure function: takes a list of messages and a token budget, returns a shortened list. Respects the tool-pairing invariant (always drop a tool call with its result). Includes property: applying again when already under budget is a no-op.

**Gate G4 — before U5:**
1. Describe recency_truncate and head_tail in one sentence each.
2. What is the tool-pairing invariant? Why would dropping a tool call without its result crash the next API call?
3. ConstraintRot found head_tail got 0% violation. Why does that make sense given where canaries are planted?

---

### U5 — Statistics

**What you'll understand:** How to measure a rate with a confidence interval (Wilson score), how to compare two conditions fairly (McNemar's test, paired design), and why you need more trials than you might think.

**Why this matters:** A number without an interval is an unverified claim. ctxcheck's whole credibility rests on honest reporting. If you publish "40% violation rate" without an interval, someone will correctly ask "how confident are you?"

---

**Step 1 — Go to Chat.**

Paste this:

> I'm measuring how often an AI agent violates a rule after context compaction. Each run is a binary outcome: violated or respected. I do n trials per condition and count k violations.
>
> 1. Why is `k/n` (the raw proportion) not enough? What does a confidence interval add?
> 2. What is the Wilson score interval? Why is it better than the normal approximation for small n or rates near 0 or 1?
> 3. I'm running the *same seeds* under two conditions (control and treatment) so I can compare paired outcomes. What is McNemar's test, and why does pairing help? Give me an intuition without the full formula.
> 4. At n=30 trials and a true rate near 50%, my 95% interval is roughly ±18 percentage points wide. What does that mean practically — can I distinguish 40% from 55%?
>
> I'm a CS student who knows Python and basic probability but has not taken a stats course.

---

**Step 2 — Build `learn/wilson.py`.**

A function `wilson_interval(k, n, z=1.96)` that returns `(lower, upper)`. Include a sanity check: at k=0, n=10, the interval does not include 0.5.

**Gate G5 — before U6:**
1. What does a confidence interval tell you, in plain English?
2. At n=30 per cell, can you tell the difference between 40% and 55% violation rates?
3. Why does pairing (same seeds, two conditions) give you more statistical power than two independent groups of the same size?

---

### U6 — Web playground

**Status: Later.** The web layer (Next.js, strata view, survival heatmap) is built in M3–M5, after the Python core is solid. Learning material will be written when we get there.

---

## When to go to Chat vs stay here

| Situation | Go to |
|---|---|
| "I don't understand this concept" | Chat |
| "I need to read a paper or article" | Chat (use the focus questions I give you) |
| "I understand it, let's build" | Code (here) |
| "The code does something I don't expect" | Code first; if still confused, Chat |
| "I want to understand a design decision (ADR)" | Code — I'll explain it in context |
| "I want to go deeper on statistics" | Chat |
| "I want to understand what the Anthropic API actually does" | Chat with the focus questions in Task 4/8 of the verification notebook |

## Reading list with focus questions

Use these when you go to Chat to read a paper or article. Don't try to absorb everything — focus on the questions.

### ConstraintRot / Governance Decay (arXiv 2606.22528)

Ask Chat to walk you through the paper focusing on:
- What exactly is a "scenario" in their benchmark? What does the scripted trajectory look like?
- What does the grader check? (The exact tool call and arguments)
- Table of results: which strategy was worst? Which was best? Why does head_tail win?
- Why did soft policies show 8x more decay than hard safety norms?

*Read this before U4 or after Gate G2, whichever feels more natural.*

### Anthropic: "Effective context engineering" (Sep 2025)

Ask Chat (or search for the article) focusing on:
- What is compaction vs tool result clearing vs context reset?
- "Start by maximising recall" — what does this mean for designing a compaction prompt?
- What does it mean for a cached prefix to be "invalidated"?

*Read this before or after U3 (cassettes), since it explains caching.*

### TRACE (arXiv 2608.06503)

Ask Chat focusing on:
- What is "execution-state mislocalization"? Give me a concrete example.
- How does this failure mode differ from forgetting a rule? (This is the `execution_state` canary type we're deferring.)

*Read after you've passed Gate G2 (canary design), so the terminology makes sense.*

---

## Gates passed (fill this in as you go)

This lives in `docs/understanding/LEDGER.md`. Update it after each gate.

| Gate | Concept | Date | One sentence that proves you got it |
|---|---|---|---|
| G0 | Tokens + context window | | |
| G1 | JSONL trace + event sourcing | | |
| G1b | Trace schema in pydantic (M1) | | |
| G2 | Canaries + conditions + deterministic grading | | |
| G3 | Cassettes + trial_index | | |
| G4 | Compaction policies + tool-pairing invariant | | |
| G5 | Wilson interval + paired design | | |
