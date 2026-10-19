"""Trace event schema — pydantic v2, single source of truth.

The JSONL trace is the source of truth for every run (see docs/ARCHITECTURE.md).
Every view the web app shows is derived by replaying these events.
Add new event types here; bump schema_version when fields change in a breaking way.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class _Base(BaseModel):
    schema_version: str = "0.1"
    run_id: str
    seq: int  # monotonically increasing; survives clock skew
    ts: str   # ISO-8601


class RunStartEvent(_Base):
    type: Literal["run_start"]
    scenario_id: str
    seed: int
    policy: str
    provider: str
    model: str
    harness_git_sha: str = "unknown"


class RunEndEvent(_Base):
    type: Literal["run_end"]
    status: Literal["ok", "error", "aborted"]


# This union grows one entry per new event type.
# The web app and graders pattern-match on `type`.
TraceEvent = RunStartEvent | RunEndEvent
