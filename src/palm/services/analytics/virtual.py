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
    op = str(transform.get("op") or "").strip()
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
    raise ValueError(f"Unsupported analytics transform op: {op!r}")


__all__ = ["apply_view_transform"]
