"""Named presets for OpenAI-compatible providers. Only facts read from the provider's docs are here.

Verified 2026-10-20 (see docs/notebook/2026-10-20-free-tier-providers.md). Not verified, so not set:
whether any of these accept `parallel_tool_calls`; hence it is off for all
presets until a live call proves it. Passing a preset's `model` is always the caller's choice: use a
model that is free on that provider (see ADR-018), never a router that picks one for you.
"""

from __future__ import annotations

from typing import Any

from ctxcheck.providers.openai_compat import OpenAICompatProvider

PRESETS: dict[str, dict[str, Any]] = {
    "openrouter": {"base_url": "https://openrouter.ai/api/v1", "api_key_env": "OPENROUTER_API_KEY"},
    "groq": {"base_url": "https://api.groq.com/openai/v1", "api_key_env": "GROQ_API_KEY"},
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "api_key_env": "GEMINI_API_KEY",
    },
    "nvidia": {"base_url": "https://integrate.api.nvidia.com/v1", "api_key_env": "NVIDIA_API_KEY"},
    # host confirmed 2026-10-20 by an authenticated GET /v1/models; free mode may train on data
    "mistral": {"base_url": "https://api.mistral.ai/v1", "api_key_env": "MISTRAL_API_KEY"},
}


def from_preset(name: str, model: str, **overrides: Any) -> OpenAICompatProvider:
    if name not in PRESETS:
        known = ", ".join(sorted(PRESETS))
        raise ValueError(f"unknown preset {name!r}; known: {known}. For others pass base_url.")
    options = {"limit_to_one_tool_call": False, **PRESETS[name], **overrides}
    return OpenAICompatProvider(model, **options)
