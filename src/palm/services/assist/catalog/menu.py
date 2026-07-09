"""Assist menu protocol — browse / search / page (0.34).

Returns a structured menu page consumed by chat (choices + input.widget=menu)
and tool profiles (items + cursors).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from palm.services.assist.service import AssistService

DEFAULT_PAGE_SIZE = 12
MAX_PAGE_SIZE = 40

_ROOT_ITEMS: list[dict[str, Any]] = [
    {
        "id": "flows",
        "kind": "section",
        "label": "Flows",
        "summary": "Browse and run catalog flows",
        "open": {"kind": "section", "id": "flows"},
    },
    {
        "id": "waiting",
        "kind": "section",
        "label": "Waiting sessions",
        "summary": "Sessions waiting for input",
        "open": {"kind": "section", "id": "waiting"},
    },
    {
        "id": "scenarios",
        "kind": "section",
        "label": "Assist scenarios",
        "summary": "Operator entry, design entry, …",
        "open": {"kind": "section", "id": "scenarios"},
    },
    {
        "id": "operator-entry",
        "kind": "scenario",
        "label": "Operator entry",
        "summary": "Guided triage menu",
        "open": {"kind": "scenario", "id": "operator-entry"},
    },
    {
        "id": "design-entry",
        "kind": "scenario",
        "label": "Design entry",
        "summary": "Create / improve flow or resource",
        "open": {"kind": "scenario", "id": "design-entry"},
    },
    {
        "id": "doctor",
        "kind": "alias",
        "label": "Doctor",
        "summary": "Engine health",
        "open": {"kind": "alias", "id": "assist/doctor"},
    },
]


def _page_size(limit: object | None) -> int:
    try:
        n = int(limit) if limit is not None else DEFAULT_PAGE_SIZE
    except (TypeError, ValueError):
        n = DEFAULT_PAGE_SIZE
    return max(1, min(n, MAX_PAGE_SIZE))


def _cursor_offset(cursor: object | None) -> int:
    if cursor is None or cursor == "":
        return 0
    try:
        return max(0, int(cursor))
    except (TypeError, ValueError):
        return 0


def _flow_label(row: dict[str, Any]) -> str:
    name = row.get("name") or row.get("flow_id") or row.get("id") or "flow"
    title = row.get("title") or row.get("summary") or row.get("description")
    label = str(name)
    if title and str(title) != label:
        return f"{label} — {str(title)[:48]}"
    return label


def _flow_id(row: dict[str, Any]) -> str:
    return str(row.get("name") or row.get("flow_id") or row.get("id") or "")


def _slice_page(
    items: list[dict[str, Any]],
    *,
    cursor: object | None,
    limit: object | None,
) -> tuple[list[dict[str, Any]], str | None, bool, int]:
    offset = _cursor_offset(cursor)
    size = _page_size(limit)
    page = items[offset : offset + size]
    next_off = offset + size
    has_more = next_off < len(items)
    next_cursor = str(next_off) if has_more else None
    return page, next_cursor, has_more, offset


def _choice_value(item: dict[str, Any]) -> str:
    open_spec = item.get("open") if isinstance(item.get("open"), dict) else {}
    kind = str(open_spec.get("kind") or item.get("kind") or "item")
    iid = str(open_spec.get("id") or item.get("id") or "")
    return f"open:{kind}:{iid}"


def _to_choices(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    choices: list[dict[str, Any]] = []
    for index, item in enumerate(items, start=1):
        choices.append(
            {
                "n": index,
                "label": str(item.get("label") or item.get("id") or f"Item {index}"),
                "value": _choice_value(item),
            }
        )
    return choices


def _filter_query(items: list[dict[str, Any]], query: str) -> list[dict[str, Any]]:
    q = (query or "").strip().lower()
    if not q:
        return items
    out: list[dict[str, Any]] = []
    for item in items:
        blob = " ".join(
            str(item.get(k) or "")
            for k in ("id", "label", "summary", "kind")
        ).lower()
        if q in blob:
            out.append(item)
    return out


def build_menu_page(
    *,
    section: str,
    query: str = "",
    cursor: object | None = None,
    limit: object | None = None,
    items: list[dict[str, Any]],
    title: str | None = None,
) -> dict[str, Any]:
    filtered = _filter_query(items, query)
    page, next_cursor, has_more, offset = _slice_page(
        filtered, cursor=cursor, limit=limit
    )
    choices = _to_choices(page)
    section_s = section or "root"
    question = title or f"Menu — {section_s}"
    if query:
        question = f"{question} (search: {query!r})"
    if filtered:
        question = f"{question} · {len(filtered)} match(es)"
    actions: list[dict[str, Any]] = []
    if has_more and next_cursor is not None:
        actions.append(
            {
                "label": "Show more",
                "alias": "assist/menu",
                "params": {
                    "section": section_s,
                    "cursor": next_cursor,
                    "limit": _page_size(limit),
                    **({"query": query} if query else {}),
                },
            }
        )
    if section_s != "root":
        actions.append({"label": "Menu home", "alias": "assist/menu", "params": {}})
    else:
        actions.append({"label": "Operator entry", "alias": "operator-entry/start"})
    actions.append({"label": "Doctor", "alias": "assist/doctor"})

    return {
        "status": "ok",
        "kind": "menu",
        "section": section_s,
        "query": query or "",
        "cursor": str(offset),
        "next_cursor": next_cursor,
        "has_more": has_more,
        "total": len(filtered),
        "page_size": _page_size(limit),
        "items": page,
        "choices": choices,
        "question": question,
        "hint": (
            "Pick a row (chip or open:kind:id). "
            "Search with params.query. Show more for the next page."
        ),
        "input": {
            "kind": "menu",
            "widget": "menu",
            "section": section_s,
            "query": query or "",
            "cursor": str(offset),
            "next_cursor": next_cursor,
            "has_more": has_more,
            "items": page,
            "choices": choices,
            "interactive": True,
            "required": False,
            "field_type": "choice",
            "prompt": question,
        },
        "actions": actions,
    }


def menu_for_assist(
    assist: AssistService,
    *,
    section: str | None = None,
    query: str = "",
    cursor: object | None = None,
    limit: object | None = None,
) -> dict[str, Any]:
    """Build a menu page for the given section."""
    sec = (section or "root").strip().lower() or "root"
    if sec in {"", "root", "home", "main"}:
        return build_menu_page(
            section="root",
            query=query,
            cursor=cursor,
            limit=limit,
            items=list(_ROOT_ITEMS),
            title="Palm menu",
        )

    if sec in {"flows", "flow", "catalog"}:
        rows = assist.list_flows() or []
        items: list[dict[str, Any]] = []
        for row in rows:
            data = row if isinstance(row, dict) else {"name": str(row)}
            if hasattr(row, "to_dict"):
                data = row.to_dict()  # type: ignore[union-attr]
            fid = _flow_id(data if isinstance(data, dict) else {})
            if not fid:
                continue
            items.append(
                {
                    "id": fid,
                    "kind": "flow",
                    "label": _flow_label(data if isinstance(data, dict) else {"name": fid}),
                    "summary": str(
                        (data or {}).get("summary")
                        or (data or {}).get("description")
                        or ""
                    ),
                    "open": {"kind": "flow", "id": fid},
                }
            )
        return build_menu_page(
            section="flows",
            query=query,
            cursor=cursor,
            limit=limit,
            items=items,
            title="Flows",
        )

    if sec in {"waiting", "wait"}:
        rows = assist.list_waiting(limit=200) or []
        items = []
        for row in rows:
            data = row if isinstance(row, dict) else {}
            sid = str(
                data.get("instance_id")
                or data.get("session_id")
                or data.get("id")
                or ""
            )
            job_id = str(data.get("job_id") or "")
            if not sid and job_id:
                sid = job_id
            if not sid:
                continue
            flow = data.get("flow_name") or data.get("flow_id") or data.get("flow")
            step = data.get("step") or data.get("current_step") or data.get("step_slug")
            short = f"{sid[:12]}…" if len(sid) > 12 else sid
            parts = []
            if flow:
                parts.append(str(flow))
            if step:
                parts.append(f"@{step}")
            parts.append(short)
            label = " · ".join(parts)
            summary_bits = [str(data.get("status") or "waiting")]
            if job_id and job_id != sid:
                summary_bits.append(f"job {job_id[:10]}")
            items.append(
                {
                    "id": sid,
                    "kind": "session",
                    "label": label,
                    "summary": " · ".join(summary_bits),
                    "open": {"kind": "session", "id": sid},
                }
            )
        return build_menu_page(
            section="waiting",
            query=query,
            cursor=cursor,
            limit=limit,
            items=items,
            title="Waiting sessions",
        )

    if sec in {"scenarios", "scenario"}:
        from palm.services.assist.registry import list_scenario_rows

        rows = list_scenario_rows()
        items = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            sid = str(row.get("scenario_id") or row.get("id") or "")
            if not sid:
                continue
            items.append(
                {
                    "id": sid,
                    "kind": "scenario",
                    "label": str(row.get("summary") or sid),
                    "summary": str(row.get("flow_id") or ""),
                    "open": {"kind": "scenario", "id": sid},
                }
            )
        return build_menu_page(
            section="scenarios",
            query=query,
            cursor=cursor,
            limit=limit,
            items=items,
            title="Scenarios",
        )

    # Unknown section → root with note
    page = build_menu_page(
        section="root",
        query=query,
        cursor=cursor,
        limit=limit,
        items=list(_ROOT_ITEMS),
        title="Palm menu",
    )
    page["hint"] = f"Unknown section {sec!r}. Showing home. Try flows, waiting, scenarios."
    return page


__all__ = [
    "DEFAULT_PAGE_SIZE",
    "MAX_PAGE_SIZE",
    "build_menu_page",
    "menu_for_assist",
]
