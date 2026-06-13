"""Flow catalog labels — mode-agnostic definition summaries."""

from __future__ import annotations

from typing import Any


def flow_detail_label(flow: Any) -> str:
    """Compact catalog/detail label for a flow definition."""
    if flow.pattern == "parallel":
        branches = flow.options.get("branches") if isinstance(flow.options, dict) else None
        if isinstance(branches, list):
            slugs = [str(item.get("slug", "?")) for item in branches if isinstance(item, dict)]
            merge = flow.options.get("merge_strategy", "all")
            return f"{len(slugs)} branches ({merge}): {', '.join(slugs)}"
        return "parallel"
    if flow.pattern == "wizard" and isinstance(flow.options, dict):
        steps = flow.options.get("steps")
        if isinstance(steps, list):
            return f"{len(steps)} steps"
    return "—"


def flow_start_hint(flow: Any) -> str | None:
    """Short operator hint shown when a flow starts."""
    detail = flow_detail_label(flow)
    return detail if detail != "—" else None