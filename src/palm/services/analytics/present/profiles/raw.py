"""raw profile — payload after path/heuristics only."""

from __future__ import annotations

from typing import Any


def present_raw(payload: Any) -> dict[str, Any]:
    return {"payload": payload}


__all__ = ["present_raw"]
