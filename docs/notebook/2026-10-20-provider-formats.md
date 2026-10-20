# 2026-10-20 — Provider request/response formats, read from the docs (for U8)

*Drafted by Claude Code. Every line below was read from the provider's own documentation on 2026-10-20 and is the basis for the adapters and their fake-response test fixtures. Nothing here has been checked against a live call.*

## Anthropic Messages API
Sources: platform.claude.com/docs/en/api/http/messages/create, .../agents-and-tools/tool-use/overview, .../handle-tool-calls.
- `POST https://api.anthropic.com/v1/messages`. Headers: `Content-Type: application/json`, `anthropic-version: 2023-06-01`, `X-Api-Key: <key>`.
- Body: `model`, `max_tokens` (required), `messages`, optional `system`, `tools`, `tool_choice`.
- The system prompt is the **top-level `system`** field. There is no "system" role for input messages.
- Consecutive same-role turns are combined into one turn by the API.
- Tools: `{name, description, input_schema}`. `tool_choice: {"type": "auto", "disable_parallel_tool_use": true}` asks for at most one tool call per turn.
- Reply: `content` is a list of blocks: `{type: "text", text}` and `{type: "tool_use", id, name, input}`; `stop_reason` is `tool_use` when a tool is wanted. `model` is reported on the reply.
- Result goes back in the next **user** message as `{type: "tool_result", tool_use_id, content, is_error?}`; `is_error: true` signals a failed or invalid call.
- `usage`: `input_tokens`, `output_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens` (plus nested detail).
- **`temperature` is deprecated.** Models released after Claude Opus 4.6 reject any value other than 1.0 with a 400 error; `top_k` and `top_p` are likewise rejected. The adapter must send none of them unless asked, and the experiment design must not assume temperature can be tuned for these models (EVAL_DESIGN says "record the temperature": record whatever the provider accepted and report it).

## OpenAI chat completions
Source: platform.openai.com/docs/guides/function-calling (and the API reference index).
- Reply `choices[0].message.tool_calls[]`: `{id, type: "function", function: {name, arguments}}`. **`arguments` is a JSON string**, not an object, and must be parsed.
- The result goes back as a message `{role: "tool", tool_call_id, content}`.
- `parallel_tool_calls: false` ensures "exactly zero or one tool is called".
- `finish_reason` is `tool_calls` when a tool is called. `usage` has `prompt_tokens`, `completion_tokens`, `total_tokens`.
- **Not verified** (so not relied on): the name of the cached-token detail field, and whether the max-tokens parameter is `max_tokens` or `max_completion_tokens` for a given model. The adapter makes the latter a constructor option.

## Consequence for the code
- Cache fields are recorded only for Anthropic. OpenAI-compatible adapters leave them `None` rather than guess a mapping.
- Malformed tool-call arguments from a model are passed on as a recognisable error, not a crash.
