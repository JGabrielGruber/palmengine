"""Rewrite / filter assistant actions for chat (Portal / WebSocket)."""

from __future__ import annotations

from typing import Any

# Agent chrome that confuses floating chat
_CHAT_NOISE_LABELS = frozenset(
    {
        "send answer",
        "inspect session",
        "resume session",
        "inspect this session",
        "open child session",
    }
)


def filter_chat_noise_actions(actions: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    if not actions:
        return []
    out: list[dict[str, Any]] = []
    for action in actions:
        if not isinstance(action, dict):
            continue
        label = str(action.get("label") or "").strip().lower()
        if label in _CHAT_NOISE_LABELS:
            continue
        out.append(dict(action))
    return out


def ensure_browse_menu_actions(payload: dict[str, Any]) -> dict[str, Any]:
    """On operator-entry intent waiting, offer Browse flows (0.34.4)."""
    status = str(payload.get("status") or "")
    if status not in {"waiting", "WAITING_FOR_INPUT"}:
        return payload
    scenario = str(payload.get("scenario_id") or "")
    compose = payload.get("compose") if isinstance(payload.get("compose"), dict) else {}
    step = str(compose.get("step") or "")
    if scenario != "operator-entry" and step != "intent":
        # still allow when choices look like operator intent menu
        choices = payload.get("choices") or []
        labels = " ".join(
            str(c.get("value") or c.get("label") or "") for c in choices if isinstance(c, dict)
        ).lower()
        if "todo-builder" not in labels and "improve-flow" not in labels:
            return payload
    actions = list(payload.get("actions") or [])
    aliases = {
        (str(a.get("alias") or ""), str((a.get("params") or {}).get("section") or ""))
        for a in actions
        if isinstance(a, dict)
    }
    if ("assist/menu", "flows") in aliases or ("assist/menu", "") in aliases:
        # may still want flows-specific
        if any(a.get("alias") == "assist/menu" for a in actions if isinstance(a, dict)):
            has_flows = any(
                isinstance(a, dict)
                and a.get("alias") == "assist/menu"
                and (a.get("params") or {}).get("section") == "flows"
                for a in actions
            )
            if has_flows:
                return payload
    out = dict(payload)
    browse = {
        "label": "Browse all flows",
        "alias": "assist/menu",
        "params": {"section": "flows"},
    }
    rest = [a for a in actions if isinstance(a, dict)]
    out["actions"] = [browse, *rest]
    return out


def rewrite_actions_for_chat(payload: dict[str, Any]) -> dict[str, Any]:
    """Map peer MCP tool actions to dispatch-friendly alias/params; drop agent chrome."""
    actions = payload.get("actions")
    if not isinstance(actions, list):
        payload = ensure_browse_menu_actions(payload)
        return payload
    rewritten: list[dict[str, Any]] = []
    for action in actions:
        if not isinstance(action, dict):
            continue
        item = dict(action)
        label = str(item.get("label") or "").strip()
        if label.lower() in _CHAT_NOISE_LABELS:
            continue
        tool = str(item.get("tool") or "")
        if item.get("alias") or item.get("path"):
            item.pop("tool", None)
            rewritten.append(item)
            continue
        if tool in {"", "palm_assist"}:
            item.pop("tool", None)
            if not item.get("params") and not item.get("alias"):
                continue
            rewritten.append(item)
            continue
        if tool == "palm_flows_create_session":
            params = dict(item.get("params") or {})
            flow_id = params.get("flow_id")
            if flow_id:
                rewritten.append(
                    {
                        "label": item.get("label") or "Run flow",
                        "params": {"flow_id": flow_id},
                    }
                )
            continue
        if tool == "palm_flows_session_resume":
            rewritten.append(
                {
                    "label": item.get("label") or "Resume",
                    "alias": "flows/session-resume",
                    "params": dict(item.get("params") or {}),
                }
            )
            continue
        if tool in {"palm_design_publish_flow", "palm_design_publish_resource"}:
            alias = "design/publish" if "flow" in tool else "design/publish-resource"
            rewritten.append(
                {
                    "label": item.get("label") or "Publish",
                    "alias": alias,
                    "params": dict(item.get("params") or {}),
                }
            )
            continue
        if tool == "palm_system_doctor":
            rewritten.append(
                {
                    "label": item.get("label") or "Doctor",
                    "alias": "assist/doctor",
                }
            )
            continue
        if tool.startswith("palm_"):
            continue
        rewritten.append(item)
    out = dict(payload)
    if rewritten:
        out["actions"] = rewritten
    elif "actions" in out:
        out.pop("actions", None)
    return ensure_browse_menu_actions(out)


__all__ = [
    "ensure_browse_menu_actions",
    "filter_chat_noise_actions",
    "rewrite_actions_for_chat",
]
