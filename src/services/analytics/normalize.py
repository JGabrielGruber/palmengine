"""ProviderResult → rows; select/limit before present (0.35.2)."""

from __future__ import annotations

import json
from typing import Any


def dotted_get(payload: Any, path: str) -> Any:
    cur: Any = payload
    for part in str(path).split("."):
        if not part:
            continue
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur


def extract_payload(envelope: dict[str, Any], *, row_path: str | None) -> Any:
    """Return invoke data after optional row_path / heuristics."""
    data = envelope.get("data")
    if row_path:
        got = dotted_get(data, row_path)
        return got if got is not None else data
    return _heuristic_payload(data)


def _heuristic_payload(payload: Any) -> Any:
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        return payload
    for key in ("items", "rows", "value"):
        val = payload.get(key)
        if isinstance(val, list):
            return val
    return payload


def coerce_rows(payload: Any) -> list[dict[str, Any]]:
    """Coerce list/dict payload into list[dict] rows."""
    if payload is None:
        return []
    if isinstance(payload, list):
        rows: list[dict[str, Any]] = []
        for item in payload:
            if isinstance(item, dict):
                rows.append(dict(item))
            else:
                rows.append({"value": item})
        return rows
    if isinstance(payload, dict):
        return [dict(payload)]
    return [{"value": payload}]


def apply_select(rows: list[dict[str, Any]], select: list[str] | None) -> list[dict[str, Any]]:
    if not select:
        return rows
    keys = [str(k) for k in select if str(k)]
    if not keys:
        return rows
    out: list[dict[str, Any]] = []
    for row in rows:
        out.append({k: row[k] for k in keys if k in row})
    return out


def apply_limit(
    rows: list[dict[str, Any]],
    *,
    limit: int | None,
    max_limit: int,
) -> tuple[list[dict[str, Any]], int, bool]:
    """Return (rows, applied_limit, truncated)."""
    cap = max_limit if limit is None else min(int(limit), max_limit)
    if cap < 0:
        cap = 0
    truncated = len(rows) > cap
    return rows[:cap], cap, truncated


def estimate_bytes(obj: Any) -> int:
    try:
        return len(json.dumps(obj, default=str).encode("utf-8"))
    except (TypeError, ValueError):
        return len(str(obj).encode("utf-8"))


__all__ = [
    "apply_limit",
    "apply_select",
    "coerce_rows",
    "dotted_get",
    "estimate_bytes",
    "extract_payload",
]
