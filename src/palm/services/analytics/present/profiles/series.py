"""series profile — x + one or more y series (post select/limit rows)."""

from __future__ import annotations

from typing import Any


def present_series(
    rows: list[dict[str, Any]],
    *,
    x_field: str | None = None,
    y_fields: list[str] | None = None,
) -> dict[str, Any]:
    """
    Build chart-friendly series.

    Defaults: first column as x; remaining numeric-ish columns as y
    (or all other keys if none look numeric).
    """
    if not rows:
        return {"x_field": x_field or "", "series": []}

    keys = _column_order(rows)
    x = x_field if x_field and x_field in keys else (keys[0] if keys else "")
    if y_fields:
        ys = [y for y in y_fields if y and y != x]
    else:
        rest = [k for k in keys if k != x]
        numeric = [k for k in rest if _looks_numeric(rows, k)]
        ys = numeric or rest

    series: list[dict[str, Any]] = []
    for y in ys:
        points: list[list[Any]] = []
        for row in rows:
            if x not in row and y not in row:
                continue
            points.append([row.get(x), row.get(y)])
        series.append({"name": y, "points": points})

    return {"x_field": x, "series": series}


def _column_order(rows: list[dict[str, Any]]) -> list[str]:
    cols: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for k in row:
            if k not in seen:
                seen.add(k)
                cols.append(k)
    return cols


def _looks_numeric(rows: list[dict[str, Any]], key: str) -> bool:
    for row in rows:
        if key not in row:
            continue
        v = row[key]
        if v is None:
            continue
        if isinstance(v, bool):
            return False
        if isinstance(v, (int, float)):
            return True
        if isinstance(v, str):
            try:
                float(v)
                return True
            except ValueError:
                return False
        return False
    return False


__all__ = ["present_series"]
