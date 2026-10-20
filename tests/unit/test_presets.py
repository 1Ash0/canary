import json

import httpx
import pytest

from ctxcheck.harness.types import Message
from ctxcheck.providers.presets import PRESETS, from_preset


def test_presets_hold_only_the_verified_base_urls() -> None:
    assert PRESETS["openrouter"]["base_url"] == "https://openrouter.ai/api/v1"
    assert PRESETS["groq"]["base_url"] == "https://api.groq.com/openai/v1"
    assert PRESETS["nvidia"]["base_url"] == "https://integrate.api.nvidia.com/v1"
    assert PRESETS["gemini"]["base_url"].endswith("/v1beta/openai/")
    assert "mistral" not in PRESETS  # host not verified yet


def test_each_preset_reads_its_own_key_variable_and_never_holds_a_key() -> None:
    assert {p["api_key_env"] for p in PRESETS.values()} == {
        "OPENROUTER_API_KEY", "GROQ_API_KEY", "GEMINI_API_KEY", "NVIDIA_API_KEY"}
    assert not any("sk-" in json.dumps(p) for p in PRESETS.values())


@pytest.mark.parametrize("name", sorted(PRESETS))
def test_a_preset_posts_to_its_chat_completions_url_without_the_parallel_flag(
    name: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: list[httpx.Request] = []
    key_var = PRESETS[name]["api_key_env"]
    monkeypatch.setenv(key_var, "test-key-1234567890")

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})

    provider = from_preset(name, "some-free-model", client=httpx.Client(
        transport=httpx.MockTransport(handler)))
    m = Message("m1", "user", "hi", "user", 1, 1)
    from ctxcheck.harness.types import ToolSpec
    provider.complete([m], [ToolSpec("t", "d", {"type": "object", "properties": {}})], {}, 0)
    base = PRESETS[name]["base_url"].rstrip("/")
    assert str(seen[0].url) == f"{base}/chat/completions"
    assert "parallel_tool_calls" not in json.loads(seen[0].content)
    assert seen[0].headers["authorization"] == "Bearer test-key-1234567890"


def test_an_unknown_preset_says_what_exists() -> None:
    with pytest.raises(ValueError, match="known: .*groq"):
        from_preset("nope", "m")
