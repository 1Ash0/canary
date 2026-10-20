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

**Decisions** (Claude Code recommended; **all five accepted by Asmit, 2026-10-20**):
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

**Status: built in M1 through the design lane (no gate).** The site, recorder and design system are in `web/` and `design/`; see `design/PROGRESS.md`.

---

### U7 — The agent loop (M2)

**M2 unit plan:** U7 agent loop and tool dispatch (this unit) → U8 provider adapters → U9 budget guard and dry-run → U10 cassettes in `src/` (a short explain-back, since you passed G3).

**What you'll understand:** What a harness actually does on every turn, how a model asks for a tool and gets the result back, when the loop stops, and why the loop is the one place where compaction can hook in.

**Why now:** Everything measured in M4 happens inside this loop. A canary is planted by a turn, compaction fires between turns, and the probe is the last turn. If the loop is a black box, you cannot say what a result means.

**Why a fake model first:** U7 builds the loop against a **scripted provider**, a stand-in that returns pre-written replies. That keeps the loop testable offline, free and deterministic. Real provider adapters are U8.

**Decisions** (Claude Code recommended; taken as accepted when Asmit said "proceed, chat done" without objecting, 2026-10-20; change any of them and the code follows):
1. **Where compaction hooks in:** check the token budget *before each model call*, and compact then if the window would go over. Alternative: after each call. Recommendation: before, because the next call is what fails if the window is too big.
2. **Stop conditions:** the model replies without a tool call (`end_turn`), or a `max_steps` safety cap is reached, or a terminal tool is called. Recommendation: all three, each recorded in `run_end`.
3. **Tools for v0.1:** a small fixed set: one or two filler tools (read a file, run a command) that return seeded text, and one **terminal tool** (for example `post_status(channel, text)`) whose arguments the grader reads. Recommendation: exactly that.
4. **Tool errors:** an unknown tool name or bad arguments become a `tool_result` with `is_error=true`, not a crash. Recommendation: yes, and test it.

**Step 1 — Go to Claude Chat.** Paste this:

> I'm building the main loop of a small agent harness in Python, for testing context compaction. I want to understand it from first principles, with small code examples. Please explain:
> 1. What happens on one turn of an agent loop? Walk through it: the harness sends the message list and the tool definitions to the model, the model replies, and so on until it stops. Draw the sequence of messages for a turn where the model calls one tool.
> 2. How does tool use work in a chat-style API like Anthropic's Messages API? What does the model's reply look like when it wants a tool (a `tool_use` block with an id and arguments), and how does my harness send the result back (a `tool_result` that refers to that id)? Why must every tool call be matched with its result?
> 3. What are the usual ways the loop ends: the model finishes without calling a tool, a step limit, or a terminal action? Why does every real harness have a step limit?
> 4. My harness will check the token budget before each model call and compact the history if it would go over. Why check before the call and not after? What goes wrong if I check after?
> 5. What should a tool dispatcher do if the model asks for a tool that doesn't exist, or passes arguments in the wrong shape? Why return an error result to the model instead of raising an exception?
> 6. I want tests to run with no network. What is a "scripted" or "fake" provider, and what makes a loop testable with one?
> I'm a second-year CS student who knows Python, understands "log as source of truth" and tokens, and is new to LLM APIs.

**Step 2 — Build `src/ctxcheck/harness/loop.py` and `tools.py` together.**
- `tools.py`: a `Tool` (name, JSON schema, function) and a `dispatch(call)` that returns a result or an error result.
- `loop.py`: `run(scenario, provider, tools, policy, budget)`:
  - builds the first messages and emits the trace events as it goes (`run_start`, `message`, `tool_call`, `tool_result`, `compaction`, `run_end`)
  - checks the budget before each model call and applies the policy hook (a no-op policy for now)
  - stops on the three conditions
- A `ScriptedProvider` that returns queued replies.
- Two-sided tests (offline): runs to `end_turn`; stops at `max_steps`; every `tool_call` has its `tool_result`; an unknown tool gives an error result and the run continues; compaction fires when the window would exceed the budget and not before; every emitted event passes `parse_event`; replaying the run through `ledger.replay` agrees with the loop's own token counts.

**Gate G7 — before U8:**
1. Describe one turn of the loop in your own words, including what the model sends back when it wants a tool.
2. Why must a `tool_call` always be paired with its `tool_result`, and what does the loop do if the model asks for a tool that doesn't exist?
3. Why does the budget check come before the model call, and why does the loop need `max_steps`?

---

### U8 — Provider adapters (M2)

**What you'll understand:** What a provider adapter is, how a model's raw HTTP reply is turned into the loop's one `ModelResponse`, how the usage numbers (including the cache fields) are read, and why the adapter is tested with no network.

**Why now:** The loop only knows the `Provider` interface. Adapters are the only code that touches a real API, so every cost, every token count and every tool call in a real run passes through them.

**Hard rule for this unit:** no live call. ADR-012 says no live model call without a `--max-usd` cap and a dry-run estimate, and the budget guard is U9. U8 builds and tests the adapters against **fake HTTP responses shaped like the real ones** (httpx's `MockTransport`). The first live call comes after U9.

**Built (2026-10-20), offline:** `providers/_http.py`, `anthropic.py`, `openai_compat.py`; `Message` gained `tool_call`, `lead_in`, `is_error` (decision 5). Things learned while building: newer Claude models reject `temperature`; OpenAI tool-call `arguments` are a JSON *string*; a provider can echo a credential back in an error, so header values are scrubbed from error text; undecodable tool arguments must be reported to the model as such. Sources: `docs/notebook/2026-10-20-provider-formats.md`.

**A gap found while planning:** the loop's assistant message stores a *text rendering* of a tool call (`[tool_call read_file {...}]`) for token counting. An adapter must send the provider a real structured tool-call block on the next request, which needs the call's name and arguments. So `Message` needs an optional `tool_call` field (decision 5).

**Decisions** (Claude Code recommends; you decide):
1. **HTTP layer:** use `httpx` directly (already a dependency) rather than the vendors' SDKs. Fewer dependencies, we control retries and timeouts, and the cassette layer sits cleanly above it.
2. **Several tool calls in one reply:** take the first, record how many were dropped in `extra`, and ask the provider for one tool at a time where the API allows it. This keeps the "one terminal action" grading rule.
3. **Usage mapping:** keep the three Anthropic input fields (`input_tokens`, `cache_read_input_tokens`, `cache_creation_input_tokens`) and map the OpenAI-style `prompt_tokens` / `completion_tokens` onto `input_tokens` / `output_tokens`. Cache fields stay `None` where the provider doesn't report them. They are recorded, never simulated.
4. **Secrets:** keys come only from environment variables, are sent as headers, and never appear in a trace, a cassette or a log line. Headers are excluded from the cassette key (ARCHITECTURE).
5. **Structured tool calls:** add an optional `tool_call` to `Message` (set on the assistant message that makes a call); the trace keeps the readable text.

**Step 1 — Go to Claude Chat.** Paste this:

> I'm writing two small HTTP client adapters in Python (using httpx, no vendor SDK): one for Anthropic's Messages API and one for an OpenAI-compatible chat completions API. Each turns a list of messages plus tool definitions into a request, and turns the JSON reply into one normalised object: some text, at most one tool call (name, arguments, id), and token usage. Please explain, with small examples:
> 1. What does a request to each API look like (endpoint, headers, body fields for model, messages, tools, max tokens)? Where does the system prompt go in each?
> 2. How does each API represent a model asking for a tool, and how do I send the tool's result back on the next request? What is different between Anthropic's content blocks and OpenAI-style `tool_calls`?
> 3. How does each API report token usage? For Anthropic, what are `input_tokens`, `cache_read_input_tokens` and `cache_creation_input_tokens`, and how do they add up to what I was billed for?
> 4. What can go wrong over HTTP that an adapter must handle: rate limits (429), server errors, overloaded responses, timeouts? Which should be retried, and how (backoff)? Which should never be retried?
> 5. How do I test an HTTP client with no network, using httpx's MockTransport? What should the fake responses contain so the test is realistic?
> 6. API keys: how should a library read them, and what are the ways one accidentally leaks into logs, error messages or saved test fixtures?
> I'm a second-year CS student who knows Python, tokens, and the idea of an agent loop with tool calls, and is new to calling LLM APIs directly.

**Step 2 — Build `providers/anthropic.py` and `providers/openai_compat.py` together.**
- Request building and response parsing as small pure functions, so they are testable without HTTP.
- A thin `complete()` that posts through an injectable `httpx.Client`.
- Retry with backoff for 429 and 5xx only; never for 4xx client errors; a hard cap on attempts.
- Two-sided tests with `MockTransport` (offline): a text reply; a one-tool-call reply; a reply with two tool calls (first taken, count recorded); usage fields mapped including cache fields present and absent; a 429 then a 200 succeeds; a 400 fails at once without retry; the API key is in the request header and **not** in the parsed response, the exception text, or `repr`.

**Gate G8 — before U9:**
1. What does an adapter do, and why does the loop only ever see a `ModelResponse`?
2. Which HTTP failures are retried and which are not, and why?
3. Where do the three Anthropic input-token fields come from, and why are the cache ones recorded rather than simulated?

---

### U9 — The budget guard (M2)

**Built (2026-10-20), offline, before your explain-back** (you asked for M2 to M5 in one go, with gates after; the order here is "code first, gate next", so treat each unit below as something to be taught back to me, not something already understood). Code: `src/ctxcheck/harness/budget.py`, tests `tests/unit/test_budget.py`.

**What you'll understand:** Why a free tier needs different guarding from a paid one, and what makes "refuse before sending" safer than "stop when it gets expensive".

**What it does:** `GuardedProvider` wraps any provider. Before every call it checks (a) the model is in a dated price table and marked free (ADR-018), (b) the per-run request and token caps, (c) the per-day caps kept in a small JSON file. After the call it records what was actually used. An unlisted or paid model is refused at a $0 budget and **nothing is sent**.

**Decisions made for you (change any, the code follows):**
1. The price table is a user-supplied dated file (`config/prices.json`, edited with `ctxcheck add-price`); nothing is hard-coded. A row without a date and a source is rejected.
2. A call's reserved tokens are `estimated input + max_tokens` and are checked **before** sending, so one big call cannot blow a cap.
3. The guard sits **under** the cassette layer, so a replay costs nothing and counts against nothing.
4. A failed call is not counted.

**Step 1 — Go to Claude Chat.** Paste this:

> I'm building a guard that sits in front of an LLM API client so a student project never spends money. I only use free models, and free tiers limit requests per day and tokens per day (and per minute), not dollars. Please explain, with small examples:
> 1. Why is "stop when the bill gets high" the wrong design when the tier is free? What are the two ways a free route can silently become paid (think model names, billing linked to a project)?
> 2. Why check limits *before* sending a request rather than after? What does a guard have to know about a request in advance, and what can it only know afterwards (token usage)?
> 3. Where should the guard sit relative to a record/replay cache, and why does that order matter for cost and for counting?
> 4. What is a sensible way to track a daily limit across separate program runs, and what goes wrong at midnight or with two processes at once?
> 5. If a request fails with a network error, should it count against the cap? Argue both sides.
> I'm a second-year CS student who knows Python and the idea of an agent loop, and is new to LLM API pricing and rate limits.

**Gate G9:**
1. Why does the guard refuse an unlisted model instead of assuming it is free, and what does it do with a paid model when the budget is $0?
2. Why is the check before the call, and what does the guard still have to do after it?
3. Where does it sit relative to cassettes, and what would break if you swapped them?

---

### U10 — Cassettes in `src/` (M2)

**Built (2026-10-20), offline.** Code: `src/ctxcheck/providers/cassette.py`, tests `tests/unit/test_cassette.py`, `tests/replay/test_m2_exit.py`. This is the port of the `learn/cassette.py` demo you passed at G3, so this gate is short.

**What changed from the demo, and why:** the key hashes the request dict **without** message ids, steps or token estimates (they can change without the request changing); the stored entry keeps the response, the date and library versions; the write is atomic (temp file then rename) so a crash never leaves half a cassette; the response carries `cassette_hit` into the trace; a replay miss raises `CassetteMiss` (a `FileNotFoundError`) and never touches the network. The M2 exit test records a run, replays it, and asserts the two traces are byte-identical except `cassette_hit`.

**Step 1 — Go to Claude Chat.** Paste this:

> I have a record/replay layer for an LLM client. The cache key is the sha256 of a canonical JSON of the request (provider, model, params, messages, tools, trial index). Please quiz me, one question at a time, and tell me where I'm wrong:
> 1. Which fields must be in the key, and which must be left out? What goes wrong if a volatile field (an id, a timestamp) is in the key? What goes wrong if a relevant field (the model, a parameter) is left out?
> 2. Why must the trial index be in the key when I run n independent trials at temperature above zero?
> 3. Why write the cache file atomically?
> 4. In CI a missing recording must be an error, never a live call. Why is a silent fallback to the network the worst option?
> 5. Two traces from a recorded run and its replay should be identical except one flag. What is that flag and what does it prove?

**Gate G10:**
1. Name one field that is deliberately not in the key, and one that must be.
2. What does `cassette_hit` prove when the record and replay traces differ only in it?
3. Why does a replay miss raise instead of calling the provider?

---

### U11 — Compaction policies in `src/` (M3)

**Built (2026-10-20), offline.** Code: `src/ctxcheck/policies/` (`units.py`, `recency.py`, `head_tail.py`, `mask.py`, `summarize.py`), tests `tests/unit/test_policies.py` and `tests/property/test_policy_invariants.py`, decisions in **ADR-019**. This extends G4 (you passed on the demo) with things the demo did not have.

**What you'll understand:** What each policy keeps and loses, why the system prompt and the current turn are never droppable, why compaction targets 60% of the budget rather than 100%, and how a property test checks an invariant on thousands of random windows.

**New ideas since the demo:**
- **Protected parts and `IrreducibleBudget`:** if the system prompt and current turn alone exceed the budget no policy can help; it raises instead of silently overrunning (invariant 1).
- **Units:** a tool call and its result are one droppable piece (invariant 2).
- **`observation_mask`** replaces old tool outputs with a short placeholder and **falls back to dropping history** when that is not enough, so its results must say when the fallback fired.
- **`llm_summary`** reads the history through the same provider stack (so the guard and cassettes apply), its prompt is a versioned artifact logged on the compaction event, and **v1 is generic on purpose**.
- **Property tests:** five invariants checked on random windows. I planted two bugs on purpose (stop pairing tool calls; ignore the budget) and both were caught.

**Step 1 — Go to Claude Chat.** Paste this:

> I'm testing context compaction policies for an LLM agent: recency truncation, keep-head-and-tail, masking old tool outputs, and LLM summarisation. Please explain, with small examples:
> 1. For each of the four, what kind of fact survives and what kind is lost? Where would a rule stated in the first user turn end up?
> 2. Why must a tool call and its result be dropped or kept together? What does an API do with an orphaned tool result?
> 3. Why compact down to, say, 60% of the limit instead of exactly the limit?
> 4. What is a property-based test (Hypothesis)? For "the compacted window never exceeds the budget unless the protected part alone does", what would the random inputs be, and what would the assertion be?
> 5. A summarisation prompt can say "keep every rule and identifier" or just "summarise". Why does that choice change what an experiment measures, and which should be the baseline?
> I'm a second-year CS student who knows Python and has met the idea of compaction.

**Gate G11:**
1. Which of the four policies keeps a rule from turn 1 at a tight budget, and which loses it? (The deterministic grid in `results/survival/grid.json` has the answer; say what it shows and what it does not.)
2. What is `IrreducibleBudget` and why does it raise?
3. Why is the baseline summary prompt generic, and what would v2 change about how to read a result?

---

### U12 — Canaries, scripted history and the grader (M4)

**Built (2026-10-20), offline.** Code: `src/ctxcheck/canaries/`, `src/ctxcheck/grading/tool_call_grader.py`, `src/ctxcheck/runner/episode.py`, tests `test_canaries.py`, `test_grader.py`, `test_experiment.py`, decisions in **ADR-020**. This puts G2 (canaries, conditions, grading) into code, with five choices that change what a result means.

**New ideas since the demo:**
- **The grader is looser than the demo on purpose:** whitespace, case, quotes and look-alike characters do not change a grade; a different value still does (ADR-020).
- **First accepted call:** a call the dispatcher rejected is not an action; no call at all is `not_applicable`, counted and given a sensitivity analysis.
- **Scripted history:** everything before the probe is replayed, not generated, so an episode costs about one live call. The cost: the harness compacts once, at the probe.
- **Survival is judged on the window the probe call saw**, excluding the probe. I got this wrong first: judging at the end of the trace scored a forgotten rule as kept because the agent's reply repeated the channel.
- **The constraint probe lists the real channel among decoys**, so the floor condition measures chance (about one in four), not zero.
- **`length_matched`** trims the oldest filler until the pre-probe window matches the treatment's post-compaction size, never touching the canary or the probe.

**Step 1 — Go to Claude Chat.** Paste this:

> I'm designing an experiment that tests whether an LLM agent still obeys a rule after its context was compacted. Conditions: floor (rule never given), control (rule given, full context), length-matched (rule given, no compaction, but the context shortened to the size of the compacted one), treatment (rule given, then compacted). Please explain, and quiz me on:
> 1. What does each condition rule out as an explanation for a failure? If treatment fails and length-matched passes, what does that tell me? If floor already "obeys", what does that tell me?
> 2. I grade by parsing the arguments of the agent's tool call, not by asking a model to judge its text. Why? What are the failure modes of each?
> 3. Formatting noise (extra spaces, different case, quotes) in the tool call arguments: should it change the grade? Where is the line between noise and a different value?
> 4. If the probe message itself contains the planted value (for example a list of channels), how does that confound a "did the rule survive" check, and how do I avoid it?
> 5. What is lost by scripting the history instead of letting the model produce it, and what is gained?
> I'm a second-year CS student with basic statistics, new to experiment design for LLM evals.

**Gate G12:**
1. Say what floor, control and length_matched each rule out, in one sentence each.
2. Why is `not_applicable` reported instead of dropped, and what is the sensitivity analysis for?
3. Why is survival judged on the window the probe saw, and what went wrong when it was judged at the end?

---

### U13 — Paired statistics and the runner (M4)

**Built (2026-10-20), offline.** Code: `src/ctxcheck/stats/paired.py`, `src/ctxcheck/runner/` (`experiment.py`, `analysis.py`, `survival.py`), `src/ctxcheck/claims.py`, tests `test_paired_stats.py`, `test_experiment.py`, `test_survival.py`, `test_claims.py`. This extends G5 (Wilson, pairing) with the tests the preregistrations use.

**New ideas since the demo:**
- **Exact McNemar:** only pairs that disagree count; under "no difference" each disagreement is a fair coin flip, so the p-value is a binomial tail. Hand check: 5 vs 0 disagreements gives 2/32 = 0.0625.
- **Paired bootstrap:** resample whole pairs to get an interval on the risk difference.
- **Benjamini-Hochberg:** with several comparisons, adjust so that a list of "significant" ones is not mostly luck.
- **Resumable runner:** each cell has a stable key; rows are appended as episodes finish; a rerun skips finished cells; a budget stop keeps partial results.
- **Simulated vs recorded** can never mix: the analysis refuses mixed rows and `check_claims.py` fails CI if a simulated row sits beside recorded ones.
- **The deterministic survival grid** answers "what does a policy keep" with no model; it does not say what an agent does next.

**Step 1 — Go to Claude Chat.** Paste this:

> I'm analysing paired binary outcomes: the same seeds run under two conditions, and the outcome per seed is violated or respected. Please make me compute by hand and quiz me on:
> 1. Exact McNemar test: with 5 seeds violated only under A and 0 only under B, what is the two-sided p-value and why? What do the seeds where both agree contribute?
> 2. A paired bootstrap interval for the risk difference: what exactly is resampled, and why resample pairs rather than each condition separately?
> 3. If I report ten comparisons and call the ones with p<0.05 "significant", what goes wrong? What does Benjamini-Hochberg change, and what does it not?
> 4. With 10 seeds per cell, what can an interval on a rate tell me, and what can't it? Why is "no significant difference" not "no difference"?
> 5. Why should I write the interpretation rules (what counts as a replication, a null, inconclusive) before running the experiment?
> I'm a second-year CS student who has seen the Wilson interval.

**Gate G13:**
1. Compute the exact McNemar p-value for 7 vs 2 by hand and say what the concordant pairs add.
2. What would make you call EXP-001 a replication, a null, or inconclusive? (Read `docs/experiments/EXP-001.md` first.)
3. Why can a simulated result and a recorded one never be analysed together here, and what enforces it?

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
| G7 | Agent loop and tool dispatch (M2) | 2026-10-20 | waived by owner, not passed (see LEDGER) |
| G8 | Provider adapters (M2) | | |
| G9 | Budget guard (M2) | | |
| G10 | Cassettes in `src/` (M2) | | |
| G11 | Compaction policies in `src/` (M3) | | |
| G12 | Canaries, scripted history and the grader (M4) | | |
| G13 | Paired statistics and the runner (M4) | | |
