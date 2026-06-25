"""Shared invoke context for local and remote execution strategies."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InvokeContext:
    """Recursion frame and correlation context for a single invoke."""

    depth: int
    chain: tuple[str, ...]
    parent_job_id: str | None