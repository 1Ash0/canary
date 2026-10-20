"""Shared HTTP plumbing for provider adapters: key reading and a POST that retries what it should.

Retried: 429, any 5xx, and network failures (timeouts, connection errors). Never retried: other 4xx,
because repeating a request the provider called invalid cannot fix it and only spends time.
Secrets: the key is read from the environment at call time and sent as a header. It is never stored
on an object. Error text uses only the provider's own error message, and every header value we sent
is scrubbed out of it first, because a provider may echo a credential back.
"""

from __future__ import annotations

import os
import time
from collections.abc import Callable
from typing import Any

import httpx

RETRYABLE_STATUS = frozenset({429}) | frozenset(range(500, 600))


class ProviderError(Exception):
    """A provider call failed for good. `status` is the HTTP status if there was one."""

    def __init__(self, message: str, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


class MissingKey(ProviderError):
    pass


def read_key(env_var: str) -> str:
    key = os.environ.get(env_var, "").strip()
    if not key:
        raise MissingKey(f"environment variable {env_var} is not set")
    return key


def _provider_message(response: httpx.Response, secrets: list[str]) -> str:
    """The provider's own explanation, truncated, with anything we sent as a header removed."""
    try:
        body = response.json()
        error = body.get("error", body) if isinstance(body, dict) else {}
        message = error.get("message") if isinstance(error, dict) else None
        text = str(message or error)
    except ValueError:
        text = response.text
    for secret in secrets:
        text = text.replace(secret, "[redacted]")
    return text[:300]


def _retry_after(response: httpx.Response, cap: float) -> float | None:
    raw = response.headers.get("retry-after")
    try:
        return min(float(raw), cap) if raw is not None else None
    except ValueError:
        return None  # an HTTP-date form is ignored; fall back to backoff


def post_json(
    client: httpx.Client,
    url: str,
    headers: dict[str, str],
    body: dict[str, Any],
    *,
    max_attempts: int = 4,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    sleep: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    """POST `body` as JSON and return the parsed reply, retrying 429/5xx/network errors."""
    last: str = "no attempt made"
    # key-like strings: each header value and each word in it (so `Bearer <key>` yields the key)
    secrets = sorted(
        {p for v in headers.values() for p in (v, *v.split()) if len(p) >= 8}, key=len, reverse=True
    )
    for attempt in range(max_attempts):
        wait = min(max_delay, base_delay * 2**attempt)
        try:
            response = client.post(url, headers=headers, json=body)
        except httpx.TransportError as exc:  # timeouts, connection resets, DNS
            last = f"network error: {type(exc).__name__}"
            if attempt + 1 < max_attempts:
                sleep(wait)
            continue

        if response.status_code < 400:
            try:
                data = response.json()
            except ValueError as exc:
                raise ProviderError("provider returned a non-JSON success reply") from exc
            if not isinstance(data, dict):
                raise ProviderError("provider returned an unexpected reply shape")
            return data

        message = _provider_message(response, secrets)
        if response.status_code not in RETRYABLE_STATUS:
            raise ProviderError(f"{response.status_code}: {message}", response.status_code)
        last = f"{response.status_code}: {message}"
        if attempt + 1 < max_attempts:
            sleep(_retry_after(response, max_delay) or wait)

    raise ProviderError(f"gave up after {max_attempts} attempts; last: {last}")
