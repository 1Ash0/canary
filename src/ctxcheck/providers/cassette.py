"""Record/replay layer for any Provider (ported from learn/cassette.py, gate G3).

The key is the sha256 of canonical JSON of the request that determines the reply: provider, model,
params, the messages' role/content/tool detail, the tools and `trial_index`. Headers and keys are
never part of it. `trial_index` is in the key on purpose: at temperature above zero, n trials need
n distinct recordings, or the variance you measure is fake.

Modes: `record` always calls the inner provider and writes; `replay` never calls anything and a miss
raises (always the mode in CI); `auto` replays if present, else records through the inner provider.
Put the budget guard *inside* (below) this layer so replays cost nothing and count against nothing.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
from collections.abc import Sequence
from dataclasses import asdict, replace
from datetime import UTC, datetime
from importlib import metadata
from pathlib import Path
from typing import Any, Literal

from ctxcheck.harness.types import Message, ModelResponse, ToolCall, ToolSpec
from ctxcheck.providers.base import Provider

Mode = Literal["record", "replay", "auto"]


class CassetteMiss(FileNotFoundError):
    """Replay asked for a request that was never recorded. Never falls through to the network."""


def _message_for_key(m: Message) -> dict[str, Any]:
    # ids, steps and token estimates are bookkeeping that can change without changing the request
    return {
        "role": m.role, "content": m.content, "call_id": m.call_id, "lead_in": m.lead_in,
        "is_error": m.is_error,
        "tool_call": asdict(m.tool_call) if m.tool_call else None,
    }


def request_dict(
    provider: str,
    model: str,
    messages: Sequence[Message],
    tools: Sequence[ToolSpec],
    params: dict[str, Any],
    trial_index: int,
) -> dict[str, Any]:
    return {
        "provider": provider, "model": model, "params": params,
        "messages": [_message_for_key(m) for m in messages],
        "tools": [asdict(t) for t in tools], "trial_index": trial_index,
    }


def make_key(request: dict[str, Any]) -> str:
    # sort_keys pins key order across machines and Python versions; without it the hash diverges
    canonical = json.dumps(request, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _response_to_json(r: ModelResponse) -> dict[str, Any]:
    return {**asdict(r), "tool_call": asdict(r.tool_call) if r.tool_call else None}


def _response_from_json(d: dict[str, Any]) -> ModelResponse:
    call = d.get("tool_call")
    return ModelResponse(
        text=d.get("text", ""),
        tool_call=ToolCall(call["id"], call["name"], call["args"]) if call else None,
        input_tokens=d.get("input_tokens", 0), output_tokens=d.get("output_tokens", 0),
        cache_read_input_tokens=d.get("cache_read_input_tokens"),
        cache_creation_input_tokens=d.get("cache_creation_input_tokens"),
        model_id=d.get("model_id", "unknown"), extra=dict(d.get("extra", {})),
    )


def _lib_versions() -> dict[str, str]:
    versions = {"python": platform.python_version()}
    for name in ("ctxcheck", "httpx", "pydantic"):
        try:
            versions[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            versions[name] = "unknown"
    return versions


class CassetteProvider:
    def __init__(
        self,
        directory: Path,
        mode: Mode,
        *,
        inner: Provider | None = None,
        provider_name: str = "unknown",
        model: str = "unknown",
    ) -> None:
        if mode in ("record", "auto") and inner is None:
            raise ValueError(f"mode {mode!r} needs an inner provider to record from")
        self.directory = directory
        self.mode = mode
        self._inner = inner
        self._provider_name = provider_name
        self._model = model
        self.hits = 0
        self.misses = 0
        directory.mkdir(parents=True, exist_ok=True)

    def __repr__(self) -> str:
        return f"CassetteProvider({self._provider_name}/{self._model}, mode={self.mode})"

    def _path(self, key: str) -> Path:
        return self.directory / f"{key}.json"

    def complete(
        self,
        messages: Sequence[Message],
        tools: Sequence[ToolSpec],
        params: dict[str, Any],
        trial_index: int,
    ) -> ModelResponse:
        request = request_dict(
            self._provider_name, self._model, messages, tools, params, trial_index
        )
        key = make_key(request)
        path = self._path(key)

        if self.mode != "record" and path.exists():
            self.hits += 1
            response = _response_from_json(json.loads(path.read_text(encoding="utf-8"))["response"])
            return _with_hit(response, True)
        if self.mode == "replay":
            self.misses += 1
            raise CassetteMiss(
                f"cassette missing: {key[:12]}... (trial {trial_index}). Record it with mode "
                f"'auto' or 'record' under a budget cap, then commit the cassette."
            )

        assert self._inner is not None
        self.misses += 1
        response = self._inner.complete(messages, tools, params, trial_index)
        entry = {
            "key": key, "request": request, "response": _response_to_json(response),
            "meta": {
                "recorded_at": datetime.now(UTC).date().isoformat(),
                "versions": _lib_versions(),
            },
        }
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(entry, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(tmp, path)  # atomic: a crash never leaves a half-written cassette
        return _with_hit(response, False)


def _with_hit(response: ModelResponse, hit: bool) -> ModelResponse:
    return replace(response, extra={**response.extra, "cassette_hit": hit})
