"""Token counting, local estimates only.

Provider-reported usage is recorded on `model_call` events. This module gives the cheap local
estimate used before a call (budget checks, dry-run cost, length matching). tiktoken's cl100k_base
is a proxy: it is not Anthropic's tokenizer, so it will not match the provider's count exactly.
"""

from __future__ import annotations

from functools import lru_cache

import tiktoken

ENCODING_NAME = "cl100k_base"


@lru_cache(maxsize=1)
def _encoding() -> tiktoken.Encoding:
    return tiktoken.get_encoding(ENCODING_NAME)


def count(text: str) -> int:
    """Local token estimate for `text`."""
    return len(_encoding().encode(text))
