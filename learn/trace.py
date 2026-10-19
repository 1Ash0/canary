"""
learn/trace.py — U1 JSONL event log

Run:  uv run python learn/trace.py

What this shows:
  1. Events are appended one at a time to a JSONL file (one JSON object per line)
  2. The file is append-only — you never edit past events, only add new ones
  3. ALL views are derived by replaying the file — not stored alongside it
  4. Adding a new view = write a new replay function, zero changes to the file

The real schema lives in src/ctxcheck/schema/events.py (pydantic v2).
This file uses plain dicts to keep the focus on the pattern, not the library.
"""

from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path


# ── writing: append one event at a time ────────────────────────────────────

def append_event(path: Path, event: dict) -> None:
    """Write one event as a JSON line. The file grows; nothing is ever rewritten."""
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")


def make_event(run_id: str, seq: int, type: str, **extra) -> dict:
    """Build an event dict. seq is the truth for ordering — not the timestamp."""
    return {
        "schema_version": "0.1",
        "run_id": run_id,
        "seq": seq,          # monotonically increasing; survives clock skew
        "ts": datetime.now(timezone.utc).isoformat(),
        "type": type,
        **extra,
    }


# ── reading: replay the file to derive views ───────────────────────────────

def replay(path: Path) -> list[dict]:
    """Read every event back, in seq order."""
    events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    return sorted(events, key=lambda e: e["seq"])  # seq is the ordering truth


# View 1: token ledger derived from message events
def view_token_ledger(events: list[dict]) -> None:
    print("\n── view: token ledger ──────────────────────────────────")
    print(f"{'seq':>4}  {'type':<18}  {'role':<10}  {'tokens':>6}  {'running':>8}")
    print("-" * 56)
    running = 0
    for e in events:
        if e["type"] == "message":
            running += e["tokens"]
            print(f"{e['seq']:>4}  {e['type']:<18}  {e['role']:<10}  {e['tokens']:>6}  {running:>8}")
        elif e["type"] == "compaction":
            tokens_after = e["tokens_after"]
            dropped = running - tokens_after
            running = tokens_after
            print(f"{e['seq']:>4}  {e['type']:<18}  {'—':<10}  {-dropped:>6}  {running:>8}  ← compaction ({e['policy']})")
    print()


# View 2: was any message dropped?  — a NEW view, zero changes to the file
def view_dropped_messages(events: list[dict]) -> None:
    print("── view: what was dropped ──────────────────────────────")
    compaction_events = [e for e in events if e["type"] == "compaction"]
    if not compaction_events:
        print("  (no compaction in this run)")
        return
    for c in compaction_events:
        kept = set(c["kept_seq"])
        message_seqs = {e["seq"] for e in events if e["type"] == "message"}
        dropped_seqs = message_seqs - kept
        print(f"  policy={c['policy']}, kept={sorted(kept)}, dropped={sorted(dropped_seqs)}")
    print()


# ── simulate a run ──────────────────────────────────────────────────────────

def simulate_run(path: Path) -> None:
    run_id = "demo-run-001"
    seq = 0

    def emit(type: str, **extra) -> None:
        nonlocal seq
        append_event(path, make_event(run_id, seq, type, **extra))
        seq += 1

    emit("run_start", scenario_id="soft_rule_01", seed=42,
         policy="recency_truncate", provider="anthropic", model="claude-haiku-4-5")

    emit("message", role="system",  tokens=120,
         content="You are a helpful assistant. Always reply in English.")
    emit("message", role="user",    tokens=15,
         content="What time is it?")
    emit("message", role="assistant", tokens=22,
         content="I don't have access to real-time data, so I can't tell you the exact time.")
    emit("message", role="user",    tokens=18,
         content="Summarise our conversation so far.")

    # compaction fires: recency_truncate drops the first user+assistant exchange
    # kept_seq lists the seq numbers of messages that survive
    emit("compaction", policy="recency_truncate",
         tokens_before=175, tokens_after=138,
         kept_seq=[0, 1, 4])   # run_start, system, last user message

    emit("message", role="assistant", tokens=30,
         content="We just started — you asked about the time and I said I don't know.")

    emit("run_end", status="ok")


# ── main ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False, mode="w") as f:
        path = Path(f.name)

    simulate_run(path)

    print(f"\n=== Raw JSONL ({path.name}) ===\n")
    for line in path.read_text(encoding="utf-8").splitlines():
        event = json.loads(line)
        # print compact: just type + seq, not the full object
        short = {k: v for k, v in event.items() if k in ("seq", "type", "role", "tokens", "policy", "status")}
        print(f"  seq={short.pop('seq'):>2}  {json.dumps(short)}")

    events = replay(path)

    view_token_ledger(events)
    view_dropped_messages(events)

    print("── key point ───────────────────────────────────────────")
    print("  Both views came from the same file.")
    print("  The file never changed — only the replay functions did.")
    print("  To add a third view (e.g. tool-call count), write a new")
    print("  replay function and run it over the same JSONL.")
    print()

    path.unlink()  # clean up temp file
