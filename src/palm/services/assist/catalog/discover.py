"""Progressive discovery search (aliases + curated starters)."""

from __future__ import annotations

from typing import Any


def discover(query: str = "", *, limit: int = 12) -> dict[str, Any]:
    """Search aliases and high-value routes (0.31.4 progressive discovery)."""
    from palm.services.assist.registry import list_mcp_path_aliases
    from palm.services.design.registry import list_design_mcp_aliases

    q = (query or "").strip().lower()
    limit = max(1, min(int(limit), 40))
    hits: list[dict[str, Any]] = []

    starters = [
        {
            "alias": "operator-entry/start",
            "kind": "alias",
            "summary": "Operator menu — triage run/design/inspect",
            "call": 'palm_assist(alias="operator-entry/start")',
        },
        {
            "alias": "assist/catalog/flows",
            "kind": "alias",
            "summary": "List runnable flows",
            "call": 'palm_assist(alias="assist/catalog/flows")',
        },
        {
            "alias": "assist/doctor",
            "kind": "alias",
            "summary": "Engine health + resource preflight",
            "call": 'palm_assist(alias="assist/doctor")',
        },
        {
            "alias": "design/publish",
            "kind": "alias",
            "summary": "One-shot publish flow definition (params.body)",
            "call": 'palm_assist(alias="design/publish", params={body: {…}})',
        },
        {
            "kind": "params",
            "summary": "Start a flow session",
            "call": 'palm_assist(params={flow_id: "coconut-npc"})',
        },
        {
            "kind": "params",
            "summary": "Continue session with plain-string answer",
            "call": 'palm_assist(params={session_id, flow_id, value})',
        },
        {
            "kind": "resource",
            "summary": "Short progressive operator card",
            "call": "read palm://agent/card",
        },
    ]

    aliases = list_mcp_path_aliases() + list_design_mcp_aliases()
    for row in aliases:
        alias = str(row.get("alias") or "")
        path = row.get("path") or []
        blob = f"{alias} {' '.join(str(p) for p in path)}".lower()
        if q and q not in blob and not any(q in str(p).lower() for p in path):
            continue
        hits.append(
            {
                "alias": alias,
                "kind": "alias",
                "path": path,
                "call": f'palm_assist(alias="{alias}", params={{…}})',
            }
        )
        if len(hits) >= limit:
            break

    if not q:
        merged = list(starters)
        seen = {h.get("alias") or h.get("call") for h in merged}
        for h in hits:
            key = h.get("alias") or h.get("call")
            if key in seen:
                continue
            merged.append(h)
            seen.add(key)
            if len(merged) >= limit:
                break
        hits = merged[:limit]
    elif not hits:
        hits = [s for s in starters if q in str(s).lower()][:limit]
        if not hits:
            hits = starters[: min(4, limit)]

    return {
        "query": query,
        "hits": hits[:limit],
        "hit_count": len(hits[:limit]),
        "hint": (
            "Use call strings with palm_assist. "
            "Load palm://agent/card for the short guide."
        ),
    }


__all__ = ["discover"]
