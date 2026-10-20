"""Verify that numbers cited in README and docs match results/ and that results are labelled.

Runs in CI and in `make check`; a mismatch exits non-zero. Logic lives in ctxcheck.claims.
"""

from __future__ import annotations

import sys
from pathlib import Path

from ctxcheck.claims import check_all

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    problems = check_all(ROOT)
    for p in problems:
        print(f"claim check failed: {p}")
    if not problems:
        print("claims: ok")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
