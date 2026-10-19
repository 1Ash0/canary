"""
learn/cassette.py — U3 record/replay layer

Run:  uv run python learn/cassette.py

What this shows:
  1. record(key, fn)  — call fn(), save the result to disk keyed by hash
  2. replay(key)      — load the saved result from disk
  3. auto(key, fn)    — record if missing, replay if present
  4. Two calls with different trial_index produce DIFFERENT cassette files
     (same request, different trials → different responses → different keys)
  5. The key is a sha256 of canonical JSON (sort_keys=True) — key order must
     be pinned or the same request produces different hashes

The real cassette layer lives in src/ctxcheck/ (built in M1).
This file uses a fake "API call" so it runs offline.
"""

from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any, Callable


# ── cassette directory ───────────────────────────────────────────────────────
# In production this is cassettes/ at the repo root.
# Here we use a temp directory so the demo cleans up after itself.

_cassette_dir: Path | None = None

def set_cassette_dir(path: Path) -> None:
    global _cassette_dir
    _cassette_dir = path
    path.mkdir(parents=True, exist_ok=True)

def _dir() -> Path:
    if _cassette_dir is None:
        raise RuntimeError("call set_cassette_dir() first")
    return _cassette_dir


# ── key ──────────────────────────────────────────────────────────────────────

def make_key(request: dict) -> str:
    """
    Canonical hash of the request dict.

    sort_keys=True is non-negotiable: without it, {"model": "x", "messages": [...]}
    and {"messages": [...], "model": "x"} produce different hashes for the same
    logical request. The hash must be deterministic across machines and Python versions.
    """
    canonical = json.dumps(request, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(canonical.encode()).hexdigest()


# ── record / replay / auto ───────────────────────────────────────────────────

def record(key: str, fn: Callable[[], Any]) -> Any:
    """Call fn(), save the result. Overwrites any existing cassette for this key."""
    result = fn()
    path = _dir() / f"{key}.json"
    path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def replay(key: str) -> Any:
    """Load a saved result. Raises FileNotFoundError if missing — never calls the API."""
    path = _dir() / f"{key}.json"
    if not path.exists():
        # In CI this is a hard failure: a missing cassette means someone forgot
        # to record it, not that we should silently spend money.
        raise FileNotFoundError(
            f"cassette missing: {path.name}\n"
            f"  Run with RECORD=1 to record it, then commit the cassette."
        )
    return json.loads(path.read_text(encoding="utf-8"))


def auto(key: str, fn: Callable[[], Any]) -> Any:
    """Record if missing, replay if present. Never overwrites an existing cassette."""
    path = _dir() / f"{key}.json"
    if path.exists():
        return replay(key)
    return record(key, fn)


# ── fake API — stands in for a real provider call ───────────────────────────

_call_count = 0  # track how many times the "API" is actually invoked

def fake_api_call(request: dict) -> dict:
    """
    Pretends to call an API. Returns a response that varies by trial_index
    so different trials produce different cassettes (simulating temperature > 0).
    """
    global _call_count
    _call_count += 1
    trial = request.get("trial_index", 0)
    return {
        "model": request["model"],
        "content": f"Response for trial {trial}: the answer is {42 + trial}.",
        "usage": {"input_tokens": 20, "output_tokens": 10},
    }


# ── demo ─────────────────────────────────────────────────────────────────────

def demo(cassette_dir: Path) -> None:
    set_cassette_dir(cassette_dir)
    global _call_count
    _call_count = 0

    base_request = {
        "provider": "anthropic",
        "model": "claude-haiku-4-5",
        "messages": [{"role": "user", "content": "What is 6 times 7?"}],
        "temperature": 1.0,
    }

    # ── 1. Record three trials ───────────────────────────────────────────────
    print("── recording 3 trials ──────────────────────────────────────────")
    keys = []
    for trial in range(3):
        request = {**base_request, "trial_index": trial}
        key = make_key(request)
        keys.append(key)
        result = record(key, lambda r=request: fake_api_call(r))
        print(f"  trial={trial}  key={key[:12]}…  response={result['content']!r}")

    print(f"\n  API calls made so far: {_call_count}  (should be 3)\n")

    # ── 2. Replay — API must NOT be called again ─────────────────────────────
    print("── replaying 3 trials ──────────────────────────────────────────")
    _call_count = 0
    for trial, key in enumerate(keys):
        result = replay(key)
        print(f"  trial={trial}  key={key[:12]}…  response={result['content']!r}")

    print(f"\n  API calls made during replay: {_call_count}  (should be 0)\n")

    # ── 3. Show that key ordering matters ────────────────────────────────────
    print("── key ordering ────────────────────────────────────────────────")
    r1 = {"model": "claude-haiku-4-5", "trial_index": 0, "messages": []}
    r2 = {"trial_index": 0, "messages": [], "model": "claude-haiku-4-5"}  # same, different order
    k1, k2 = make_key(r1), make_key(r2)
    print(f"  dict A key:  {k1[:20]}…")
    print(f"  dict B key:  {k2[:20]}…")
    print(f"  same hash?   {k1 == k2}  (sort_keys=True makes this True)")
    print()

    # ── 4. Show that different trial_index → different key ───────────────────
    print("── trial_index changes the key ─────────────────────────────────")
    r_t0 = {**base_request, "trial_index": 0}
    r_t1 = {**base_request, "trial_index": 1}
    print(f"  trial=0 key: {make_key(r_t0)[:20]}…")
    print(f"  trial=1 key: {make_key(r_t1)[:20]}…")
    print(f"  same key?    {make_key(r_t0) == make_key(r_t1)}  (must be False)")
    print()

    # ── 5. Missing cassette raises — never silently calls the API ────────────
    print("── missing cassette raises FileNotFoundError ───────────────────")
    try:
        replay("0" * 64)  # a key that was never recorded
    except FileNotFoundError as e:
        print(f"  FileNotFoundError: {str(e).splitlines()[0]}")
    print()

    # ── 6. Files written ─────────────────────────────────────────────────────
    files = sorted(_dir().glob("*.json"))
    print(f"── cassette files written ({len(files)}) ─────────────────────")
    for f in files:
        print(f"  {f.name}")


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as tmp:
        demo(Path(tmp))
