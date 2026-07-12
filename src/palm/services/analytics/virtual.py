"""Virtual analytics views — apply declared transform ops to row lists."""

from __future__ import annotations

from typing import Any

from palm.common.transforms.rules.count_by import CountByRule
from palm.core.transform.base import TransformContext


def apply_view_transform(
    rows: list[dict[str, Any]],
    transform: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    if not transform:
        return list(rows)
    op = str(transform.get("op") or transform.get("kind") or "").strip().lower()
    if op == "count_by":
        field = transform.get("field")
        if not field:
            raise ValueError("count_by requires field")
        ctx = TransformContext(original=list(rows))
        result = CountByRule.from_options(field=str(field)).apply(ctx)
        value = result.value
        if not isinstance(value, list):
            return []
        return [r for r in value if isinstance(r, dict)]

    # 0.40.4 — lightweight pure ops (no new engine types)
    if op in {"filter_eq", "where_eq"}:
        field = transform.get("field")
        if not field:
            raise ValueError(f"{op} requires field")
        want = transform.get("value")
        if "value" not in transform and "eq" in transform:
            want = transform.get("eq")
        key = str(field)
        return [
            r
            for r in rows
            if isinstance(r, dict) and r.get(key) == want
        ]

    if op in {"limit", "take", "head"}:
        try:
            n = int(transform.get("n") or transform.get("limit") or transform.get("count") or 10)
        except (TypeError, ValueError):
            n = 10
        n = max(0, n)
        return list(rows)[:n]

    if op in {"sort_by", "order_by"}:
        field = transform.get("field")
        if not field:
            raise ValueError(f"{op} requires field")
        reverse = bool(transform.get("desc") or transform.get("reverse"))
        key = str(field)

        def _key(row: dict[str, Any]) -> Any:
            val = row.get(key)
            return (val is None, val)

        return sorted(
            [r for r in rows if isinstance(r, dict)],
            key=_key,
            reverse=reverse,
        )

    raise ValueError(f"Unsupported analytics transform op: {op!r}")


__all__ = ["apply_view_transform"]
