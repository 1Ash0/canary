import pytest

from ctxcheck import tokens


@pytest.fixture(scope="module")
def encoding_available() -> None:
    # tiktoken downloads its vocabulary on first use; offline tests must not need the network.
    try:
        tokens.count("probe")
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"tiktoken vocabulary not cached: {exc}")


def test_empty_string_is_zero_tokens(encoding_available: None) -> None:
    assert tokens.count("") == 0


def test_more_text_is_never_fewer_tokens(encoding_available: None) -> None:
    short = "A typical English sentence."
    assert tokens.count(short + " " + short) > tokens.count(short) > 0


def test_count_is_deterministic(encoding_available: None) -> None:
    text = "def add(a, b): return a + b"
    assert tokens.count(text) == tokens.count(text)
