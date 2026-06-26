"""
Commit result summaries — compact node IDs for operator agents.
"""

from __future__ import annotations

from typing import Any


def summarize_commit_result(result: Any) -> dict[str, Any] | None:
    """Extract common node identifiers from a wizard commit result."""
    if not isinstance(result, dict):
        return None

    summary: dict[str, Any] = {}

    for key in ("main_node", "node"):
        node = result.get(key)
        if isinstance(node, dict) and node.get("id"):
            summary["main_node_id"] = node["id"]
            title = node.get("title")
            if isinstance(title, str) and title:
                summary["main_node_title"] = title
            break

    for list_key in ("captured_nodes", "nodes", "related_nodes"):
        items = result.get(list_key)
        if not isinstance(items, list):
            continue
        ids = [
            str(item["id"])
            for item in items
            if isinstance(item, dict) and item.get("id")
        ]
        if ids:
            summary["node_ids"] = ids
            break

    return summary or None


__all__ = ["summarize_commit_result"]