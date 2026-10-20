# 2026-10-20 — Free-tier providers: what was verified and what was not

*Drafted by Claude Code. Free-tier terms change often; everything below was read from the cited page on 2026-10-20. "Not verified" means exactly that: do not rely on it.*

## Verified
- **OpenRouter** (openrouter.ai/docs/faq, /docs/api-reference/limits): a unified API over many providers' models, pass-through pricing. It implements the OpenAI `/chat/completions` format. Free models (IDs ending `:free`): **20 requests/min; 50 requests/day if less than 10 credits ever purchased, 1000/day with at least 10.** Prompts and completions are not logged by default; OpenRouter is a proxy, so the underlying provider's own policy also applies. `openrouter/free` is a router that picks a free model for you.
- **Gemini API** (ai.google.dev/gemini-api/docs/rate-limits, /terms): limits are per project, per model, and visible only in AI Studio (the docs page gives no free-tier numbers; "specified rate limits are not guaranteed"). RPD resets at midnight Pacific. **Unpaid quota: Google uses submitted prompts and responses to improve its products and models, and human reviewers may read them.** Paid quota does not. (EEA/UK/Switzerland get the paid-style terms even on unpaid quota.)
- **Groq** (console.groq.com/docs/rate-limits): limits are per model. Row seen for `openai/gpt-oss-120b`: `30 | 1K | 8K | 200K`. The column headers were lost in extraction; I read them as RPM, RPD, TPM, TPD, which is an inference. Response headers: `x-ratelimit-limit-requests` is always requests per day, `x-ratelimit-limit-tokens` is always tokens per minute; a 429 carries `retry-after` in seconds.
- **NVIDIA NIM / build.nvidia.com** (docs.api.nvidia.com/nim/docs/api-quickstart, developer forum): a key comes from a model page ("Get API Key", NVIDIA Developer Program). The numbers come from **forum posts by users, not official docs**: about **40 requests/min and 1,000 credits** on the free tier; moderators say the limit depends on model, use and overall traffic, and cannot be raised on that tier.
- **Mistral** (docs.mistral.ai/admin/billing-usage/usage-limits): a "free mode" exists with included monthly usage; limits are per model (requests/second, tokens/minute) and shown in the console's Limits page.

## Not verified
- Mistral's free-plan numbers and data/training policy.
- NVIDIA's official terms and limits; whether the free tier is for prototyping only.
- Groq's plan (free vs paid) for the table row and the column headers.
- Gemini's per-model free numbers.
- Whether each provider's endpoint is OpenAI-compatible and whether each specific free model calls tools reliably. Check each before use.

## Consequences recorded for the design
1. Free tiers cap **requests per day and tokens per day**, which bind far earlier than money. The budget guard (U9) needs request and token caps, not only `--max-usd`.
2. Free models change and disappear; always record `model_id_reported`, never run an experiment through a router that picks the model.
3. Prompts on some free tiers may be used for training or read by humans. Only synthetic, seeded scenarios may be sent. Nothing personal or private.
4. Cassettes make the limits a recording-speed problem only: record once, replay free forever.

## Follow-up, same day: endpoints, tool calling, terms (second pass)
Verified from the providers' own pages:
- **OpenRouter:** base URL `https://openrouter.ai/api/v1`. Tool calling is model-dependent; filter models with `supported_parameters=tools`. The `tools` parameter must be sent on every request.
- **Groq:** OpenAI-compatible at `https://api.groq.com/openai/v1`. The compatibility page notes `N`, if supplied, must equal 1. Tool-calling detail not captured.
- **Gemini:** OpenAI-compatible at `https://generativelanguage.googleapis.com/v1beta/openai/`, key as `Authorization: Bearer`. Function calling via `tools` and `tool_choice: "auto"` is shown.
- **NVIDIA:** `POST https://integrate.api.nvidia.com/v1/chat/completions`. Trial terms: **internal testing and evaluation only, not production**; the catalogue is "a no-cost trial experience", prototyping, research, development and testing. Whether publishing benchmark results derived from it is allowed is **not verified**: read the terms before publishing numbers from NVIDIA-hosted models.
- **Mistral:** `POST /v1/chat/completions` (host name not shown on the page, so not recorded as a preset); supports `parallel_tool_calls` (default true) and `tool_choice` of auto, none, any, required. **Free mode: "we may use your data (input and output) to train our AI models"**; the pricing page shows no opt-out on the Free plan (opt-out is listed for paid plans).

Still not verified: that any of these accept `parallel_tool_calls: false` (so the adapter option `limit_to_one_tool_call` is off in every preset until a live call shows it is accepted); which specific free models call tools reliably; Mistral free numbers.

Decision taken: ADR-018, zero spend.
