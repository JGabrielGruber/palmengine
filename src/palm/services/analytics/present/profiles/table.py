"""table profile — columns + row arrays."""

from __future__ import annotations

from typing import Any


def present_table(rows: list[dict[str, Any]]) -> dict[str, Any]:
    columns: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for k in row:
            if k not in seen:
                seen.add(k)
                columns.append(k)
    body = [[row.get(c) for c in columns] for row in rows]
    return {"columns": columns, "rows": body}


__all__ = ["present_table"]
