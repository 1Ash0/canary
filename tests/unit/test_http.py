"""Retry rules, error text and key handling, all against a fake transport (no network)."""

import httpx
import pytest

from ctxcheck.providers._http import MissingKey, ProviderError, post_json, read_key

KEY = "sk-test-SECRET-1234567890"
URL = "https://example.test/v1/thing"
HEADERS = {"X-Api-Key": KEY}


def client_for(*statuses: int | Exception, bodies: dict[int, dict] | None = None):
    """A client whose transport answers with each status in turn; records every request."""
    seen: list[httpx.Request] = []
    queue = list(statuses)

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        item = queue.pop(0)
        if isinstance(item, Exception):
            raise item
        default = {"ok": True} if item < 400 else {"error": {"message": "nope"}}
        body = (bodies or {}).get(item, default)
        return httpx.Response(item, json=body)

    return httpx.Client(transport=httpx.MockTransport(handler)), seen


def post(client: httpx.Client, **kw):
    sleeps: list[float] = []
    out = post_json(client, URL, HEADERS, {"a": 1}, sleep=sleeps.append, **kw)
    return out, sleeps


def test_success_returns_the_parsed_json_and_sends_the_headers_and_body() -> None:
    client, seen = client_for(200)
    out, sleeps = post(client)
    assert out == {"ok": True} and sleeps == []
    assert seen[0].headers["x-api-key"] == KEY and seen[0].content == b'{"a":1}'


def test_a_429_is_retried_then_succeeds() -> None:
    client, seen = client_for(429, 200)
    out, sleeps = post(client)
    assert out == {"ok": True} and len(seen) == 2 and len(sleeps) == 1


def test_5xx_including_overloaded_is_retried() -> None:
    client, seen = client_for(500, 503, 529, 200)
    out, sleeps = post(client, max_attempts=5)
    assert out == {"ok": True} and len(seen) == 4 and len(sleeps) == 3


def test_a_400_is_never_retried() -> None:
    client, seen = client_for(400, 200)
    with pytest.raises(ProviderError) as exc:
        post(client)
    assert len(seen) == 1 and exc.value.status == 400 and "nope" in str(exc.value)


@pytest.mark.parametrize("status", [401, 403, 404, 422])
def test_other_client_errors_are_never_retried(status: int) -> None:
    client, seen = client_for(status, 200)
    with pytest.raises(ProviderError):
        post(client)
    assert len(seen) == 1


def test_it_gives_up_after_max_attempts_and_says_so() -> None:
    client, seen = client_for(500, 500, 500)
    with pytest.raises(ProviderError, match="gave up after 3 attempts"):
        post(client, max_attempts=3)
    assert len(seen) == 3


def test_backoff_doubles_and_is_capped() -> None:
    client, _ = client_for(500, 500, 500, 500, 200)
    _, sleeps = post(client, max_attempts=5, base_delay=1.0, max_delay=3.0)
    assert sleeps == [1.0, 2.0, 3.0, 3.0]


def test_retry_after_is_honoured_but_capped() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if not handler.sent:  # type: ignore[attr-defined]
            handler.sent = True  # type: ignore[attr-defined]
            slow = {"error": {"message": "slow"}}
            return httpx.Response(429, headers={"retry-after": "999"}, json=slow)
        return httpx.Response(200, json={"ok": True})

    handler.sent = False  # type: ignore[attr-defined]
    client = httpx.Client(transport=httpx.MockTransport(handler))
    _, sleeps = post(client, max_delay=7.0)
    assert sleeps == [7.0]


def test_network_errors_are_retried() -> None:
    client, seen = client_for(httpx.ConnectTimeout("t"), httpx.ConnectError("c"), 200)
    out, sleeps = post(client)
    assert out == {"ok": True} and len(seen) == 3 and len(sleeps) == 2


def test_persistent_network_failure_ends_in_a_provider_error() -> None:
    client, _ = client_for(httpx.ConnectError("c"), httpx.ConnectError("c"))
    with pytest.raises(ProviderError, match="network error: ConnectError"):
        post(client, max_attempts=2)


def test_a_non_json_success_reply_is_an_error() -> None:
    html = httpx.MockTransport(lambda r: httpx.Response(200, text="<html>"))
    client = httpx.Client(transport=html)
    with pytest.raises(ProviderError, match="non-JSON"):
        post(client)


def test_a_key_echoed_back_by_the_provider_is_scrubbed_from_the_error() -> None:
    echo = {"error": {"message": f"Incorrect API key provided: {KEY}. See docs."}}
    for status in (401, 500):  # a non-retryable path and the give-up path
        client, _ = client_for(status, status, bodies={status: echo})
        with pytest.raises(ProviderError) as exc:
            post(client, max_attempts=2)
        assert KEY not in str(exc.value) and KEY not in repr(exc.value)
    assert "[redacted]" in str(exc.value)  # the provider's wording survives, minus the secret


def test_a_bearer_key_echoed_without_the_word_bearer_is_scrubbed() -> None:
    echo = {"error": {"message": f"Incorrect API key provided: {KEY}"}}
    client, _ = client_for(401, bodies={401: echo})
    with pytest.raises(ProviderError) as exc:
        post_json(client, URL, {"Authorization": f"Bearer {KEY}"}, {}, sleep=lambda s: None)
    assert KEY not in str(exc.value) and "[redacted]" in str(exc.value)


def test_the_key_is_scrubbed_from_a_non_json_error_body_too() -> None:
    client = httpx.Client(transport=httpx.MockTransport(
        lambda r: httpx.Response(401, text=f"<html>bad key {KEY}</html>")
    ))
    with pytest.raises(ProviderError) as exc:
        post(client)
    assert KEY not in str(exc.value)


def test_error_text_is_built_from_the_response_never_from_our_request() -> None:
    client, seen = client_for(401)
    with pytest.raises(ProviderError) as exc:
        post(client)
    assert seen[0].headers["x-api-key"] == KEY  # it was sent...
    assert KEY not in str(exc.value)  # ...and is not in what we raise


def test_read_key_reads_the_environment_and_never_echoes_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CTXCHECK_TEST_KEY", f"  {KEY}  ")
    assert read_key("CTXCHECK_TEST_KEY") == KEY
    monkeypatch.delenv("CTXCHECK_TEST_KEY")
    with pytest.raises(MissingKey) as exc:
        read_key("CTXCHECK_TEST_KEY")
    assert "CTXCHECK_TEST_KEY" in str(exc.value) and KEY not in str(exc.value)


def test_a_blank_key_counts_as_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CTXCHECK_TEST_KEY", "   ")
    with pytest.raises(MissingKey):
        read_key("CTXCHECK_TEST_KEY")
