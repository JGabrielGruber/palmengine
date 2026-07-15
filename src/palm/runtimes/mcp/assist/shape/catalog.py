"""Assistant shaping for catalog / doctor / discover / waiting results."""

from __future__ import annotations

from typing import Any


def shape_menu_assistant(result: dict[str, Any]) -> dict[str, Any]:
    """Pass through structured menu page for chat/tool consumers (0.34)."""
    if not isinstance(result, dict):
        return {
            "status": "ok",
            "question": "Menu unavailable.",
            "hint": "Retry assist/menu.",
        }
    out = dict(result)
    out.setdefault("status", "ok")
    if out.get("choices") and not out.get("input"):
        out["input"] = {
            "kind": "menu",
            "widget": "menu",
            "choices": out.get("choices"),
            "items": out.get("items"),
            "section": out.get("section"),
            "has_more": out.get("has_more"),
            "next_cursor": out.get("next_cursor"),
            "interactive": True,
            "field_type": "choice",
        }
    return out


def shape_discover_assistant(result: dict[str, Any]) -> dict[str, Any]:
    """Short discover turn — progressive disclosure without a second MCP tool."""
    hits = result.get("hits") if isinstance(result.get("hits"), list) else []
    lines: list[str] = []
    for hit in hits[:8]:
        if not isinstance(hit, dict):
            continue
        call = hit.get("call") or hit.get("alias") or ""
        summary = hit.get("summary") or ""
        if summary:
            lines.append(f"- {call}: {summary}")
        else:
            lines.append(f"- {call}")
    body = "\n".join(lines) if lines else "No hits — try a broader query or read palm://agent/card."
    query = result.get("query") or ""
    return {
        "status": "ok",
        "question": f"Discover results{f' for {query!r}' if query else ''} ({len(hits)}).",
        "hint": str(result.get("hint") or "Use palm_assist with the call strings above."),
        "hits": hits,
        "hit_count": result.get("hit_count", len(hits)),
        "actions": [
            {"label": "Operator card", "hint": "read palm://agent/card"},
            {"label": "List flows", "alias": "assist/catalog/flows"},
            {"label": "Doctor", "alias": "assist/doctor"},
            {"label": "Operator entry", "alias": "operator-entry/start"},
        ],
        "preview": body,
    }


def shape_doctor_assistant(result: Any) -> dict[str, Any]:
    """Compact doctor report for assist-only agents (0.31.2)."""
    report = result if isinstance(result, dict) else {"value": result}
    preflight = report.get("resource_preflight") if isinstance(report, dict) else None
    hint = "Engine health OK." if report else "Doctor returned no data."
    if isinstance(preflight, dict):
        missing = preflight.get("rest_missing_base_url")
        if missing:
            hint = f"REST resources missing base_url: {missing!r}. Fix params or env."
        elif preflight.get("kv") or preflight.get("file"):
            hint = "See resource_preflight for kv/file backends."
    return {
        "status": "ok",
        "question": "Palm doctor report.",
        "hint": hint,
        "doctor": report,
        "actions": [
            {"label": "List flows", "alias": "assist/catalog/flows"},
            {"label": "List waiting", "alias": "assist/catalog/waiting"},
            {"label": "Start operator entry", "alias": "operator-entry/start"},
        ],
    }


def shape_flows_catalog_assistant(result: Any) -> dict[str, Any]:
    """List flows as a short assistant turn (0.31.2)."""
    rows = result if isinstance(result, list) else []
    names: list[str] = []
    for row in rows[:30]:
        if isinstance(row, dict):
            name = row.get("name") or row.get("flow_id") or row.get("id")
            if name is not None:
                names.append(str(name))
        else:
            names.append(str(row))
    preview = ", ".join(names[:12])
    if len(names) > 12:
        preview += ", …"
    return {
        "status": "ok",
        "question": f"Catalog: {len(rows)} flow(s).",
        "hint": (
            f"Known: {preview}. Start with palm_assist(params={{flow_id: \"…\"}})."
            if preview
            else "No flows listed."
        ),
        "flow_count": len(rows),
        "flow_names": names,
        "actions": [
            {
                "label": "Start coconut NPC",
                "tool": "palm_assist",
                "params": {"flow_id": "coconut-npc"},
            },
            {"label": "Operator entry", "alias": "operator-entry/start"},
            {"label": "Publish flow", "alias": "design/publish"},
        ],
    }


def shape_waiting_assistant(
    result: Any,
    *,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Waiting jobs/sessions as assistant turn (0.31.2 / 0.34.5 resume chips)."""
    del params  # reserved for future filters
    rows: list[Any]
    if isinstance(result, list):
        rows = result
    elif isinstance(result, dict) and isinstance(result.get("jobs"), list):
        rows = result["jobs"]
    elif isinstance(result, dict) and isinstance(result.get("waiting"), list):
        rows = result["waiting"]
    else:
        rows = []
    slim: list[dict[str, Any]] = []
    choices: list[dict[str, Any]] = []
    resume_actions: list[dict[str, Any]] = []
    for index, row in enumerate(rows[:20], start=1):
        if not isinstance(row, dict):
            continue
        sid = row.get("instance_id") or row.get("session_id") or row.get("id")
        if sid is None:
            continue
        sid_s = str(sid)
        flow = row.get("flow_name") or row.get("flow_id") or row.get("flow")
        step = row.get("step") or row.get("current_step") or row.get("step_slug")
        entry = {
            k: row[k]
            for k in (
                "session_id",
                "instance_id",
                "job_id",
                "flow",
                "flow_id",
                "flow_name",
                "status",
                "step",
            )
            if row.get(k) is not None
        }
        if "instance_id" not in entry and "session_id" not in entry:
            entry["session_id"] = sid_s
        slim.append(entry)
        short = f"{sid_s[:12]}…" if len(sid_s) > 12 else sid_s
        label_parts = ["Resume"]
        if flow:
            label_parts.append(str(flow))
        if step:
            label_parts.append(f"@{step}")
        label_parts.append(short)
        label = " · ".join(label_parts)
        choices.append(
            {
                "n": index,
                "label": label,
                "value": f"open:session:{sid_s}",
            }
        )
        open_params: dict[str, Any] = {"kind": "session", "id": sid_s}
        if flow:
            open_params["flow_id"] = str(flow)
        resume_actions.append(
            {
                "label": label if len(label) < 40 else f"Resume {flow or short}",
                "alias": "assist/open",
                "params": open_params,
            }
        )
    actions: list[dict[str, Any]] = list(resume_actions[:8])
    actions.extend(
        [
            {
                "label": "Waiting menu",
                "alias": "assist/menu",
                "params": {"section": "waiting"},
            },
            {"label": "Browse flows", "alias": "assist/menu", "params": {"section": "flows"}},
            {"label": "Operator entry", "alias": "operator-entry/start"},
        ]
    )
    out: dict[str, Any] = {
        "status": "ok",
        "kind": "menu",
        "section": "waiting",
        "question": f"{len(rows)} session(s) waiting for input.",
        "hint": (
            "Tap a Resume chip to open that session, or use the Waiting menu."
            if rows
            else "Nothing waiting."
        ),
        "waiting_count": len(rows),
        "waiting": slim,
        "actions": actions,
    }
    if choices:
        items = []
        for s, c in zip(slim, choices, strict=False):
            iid = str(s.get("instance_id") or s.get("session_id") or "")
            items.append(
                {
                    "id": iid,
                    "kind": "session",
                    "label": c["label"],
                    "open": {"kind": "session", "id": iid},
                }
            )
        out["choices"] = choices
        out["items"] = items
        out["input"] = {
            "kind": "menu",
            "widget": "menu",
            "section": "waiting",
            "choices": choices,
            "interactive": True,
            "field_type": "choice",
            "prompt": f"{len(rows)} waiting session(s)",
        }
    return out


__all__ = [
    "shape_discover_assistant",
    "shape_doctor_assistant",
    "shape_flows_catalog_assistant",
    "shape_menu_assistant",
    "shape_waiting_assistant",
]
