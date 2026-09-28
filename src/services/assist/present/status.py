"""Status normalization for assistant turns."""

from __future__ import annotations


def human_status(raw: object | None) -> str:
    if raw is None:
        return "running"
    text = str(raw).upper()
    if text == "WAITING_FOR_INPUT":
        return "waiting"
    if text in {"SUCCEEDED", "SUCCESS"}:
        return "complete"
    if text in {"FAILED", "CANCELLED"}:
        return "failed"
    if text == "RUNNING":
        return "running"
    return str(raw).lower()


__all__ = ["human_status"]
