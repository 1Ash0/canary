"""Canary packs. A new pack is one module with `build(seed, plant=...)`, registered here."""

from __future__ import annotations

from collections.abc import Callable

from ctxcheck.canaries import constraint, identifier, multi
from ctxcheck.canaries.base import Built, trim_to_length, window_tokens_before_probe

PACKS: dict[str, Callable[..., Built]] = {
    "constraint": constraint.build,
    "identifier": identifier.build,
    **multi.BUILDERS,  # multi_channel, multi_code, multi_deploy: one history, three facts
}


def build_pack(name: str, seed: int, **options: object) -> Built:
    if name not in PACKS:
        raise ValueError(f"unknown pack {name!r}; known: {', '.join(sorted(PACKS))}")
    return PACKS[name](seed, **options)


__all__ = ["PACKS", "Built", "build_pack", "trim_to_length", "window_tokens_before_probe"]
