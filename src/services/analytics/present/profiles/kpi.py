"""kpi profile — single aggregate over one field (delta always null in 0.35)."""

from __future__ import annotations

from typing import Any, Literal

Agg = Literal["sum", "count", "avg", "min", "max"]
_AGGS = frozenset({"sum", "count", "avg", "min", "max"})


def present_kpi(
    rows: list[dict[str, Any]],
    *,
    field: str | None = None,
    agg: str = "sum",
    label: str | None = None,
    unit: str | None = None,
) -> dict[str, Any]:
    op = str(agg or "sum").lower()
    if op not in _AGGS:
        op = "sum"

    if op == "count" and not field:
        value: Any = float(len(rows))
        used = "count"
    else:
        key = field or _default_field(rows)
        used = key or ""
        nums = _numbers(rows, key) if key else []
        value = _aggregate(nums, op)  # type: ignore[arg-type]

    return {
        "label": label or (f"{op}({used})" if used else op),
        "value": value,
        "unit": unit,
        "format": "number",
        "delta": None,
        "agg": op,
        "field": used or None,
    }


def _default_field(rows: list[dict[str, Any]]) -> str | None:
    for row in rows:
        for k, v in row.items():
            if isinstance(v, bool):
                continue
            if isinstance(v, int | float):
                return k
    if rows:
        return next(iter(rows[0]), None)
    return None


def _numbers(rows: list[dict[str, Any]], key: str) -> list[float]:
    out: list[float] = []
    for row in rows:
        if key not in row:
            continue
        v = row[key]
        if v is None or isinstance(v, bool):
            continue
        if isinstance(v, int | float):
            out.append(float(v))
        elif isinstance(v, str):
            try:
                out.append(float(v))
            except ValueError:
                continue
    return out


def _aggregate(nums: list[float], op: Agg) -> float | None:
    if op == "count":
        return float(len(nums))
    if not nums:
        return None
    if op == "sum":
        return float(sum(nums))
    if op == "avg":
        return float(sum(nums) / len(nums))
    if op == "min":
        return float(min(nums))
    if op == "max":
        return float(max(nums))
    return None


__all__ = ["present_kpi"]
