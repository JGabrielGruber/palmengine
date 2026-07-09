"""Default, session, and resource CTAs for assistant turns."""

from __future__ import annotations

from typing import Any

from palm.services.assist.present.status import human_status

VERB_ACTION_LABELS: dict[str, str] = {
    "input": "Send answer",
    "backtrack": "Go back",
    "resume": "Resume session",
    "handoff": "Hand off to business flow",
    "cancel": "Cancel session",
}


def default_turn_actions(
    payload: dict[str, Any],
    composed: dict[str, Any],
    *,
    session_id: str | None,
    flow_id: str | None,
) -> list[dict[str, Any]]:
    """One lean CTA for waiting or terminal turns when nothing else set."""
    status = str(payload.get("status") or "")
    if status == "waiting" and session_id:
        params: dict[str, Any] = {"session_id": session_id}
        if flow_id:
            params["flow_id"] = flow_id
        return [
            {
                "label": "Send answer",
                "tool": "palm_assist",
                "params": params,
            }
        ]
    if status == "complete":
        actions: list[dict[str, Any]] = []
        if flow_id:
            actions.append(
                {
                    "label": "Run again",
                    "tool": "palm_assist",
                    "params": {"flow_id": flow_id},
                }
            )
        actions.append(
            {"label": "Start operator entry", "alias": "operator-entry/start"}
        )
        return actions
    return []


def resource_assistant_actions(
    composed: dict[str, Any],
    *,
    session_id: str | None,
    flow_id: str | None,
) -> list[dict[str, Any]]:
    """CTAs when a resource step failed or is waiting for resume."""
    if not session_id:
        return []
    has_error = bool(composed.get("resource_error"))
    step_kind = composed.get("step_kind")
    status = str(composed.get("status") or "").upper()
    waiting = status in {"WAITING_FOR_INPUT", "WAITING", "RUNNING"} or human_status(
        composed.get("status")
    ) in {"waiting", "running"}
    if not has_error and not (step_kind == "resource" and waiting):
        return []
    params: dict[str, Any] = {"session_id": session_id}
    if flow_id:
        params["flow_id"] = flow_id
    actions: list[dict[str, Any]] = [
        {
            "label": "Resume resource step",
            "alias": "flows/session-resume",
            "params": dict(params),
        },
        {
            "label": "Doctor (resource preflight)",
            "alias": "assist/doctor",
        },
    ]
    if has_error:
        actions.append(
            {
                "label": "Publish missing resource",
                "alias": "design/publish-resource",
            }
        )
    return actions


def merge_assistant_actions(
    *lists: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    """Merge action lists; first wins on (alias|tool|path, label)."""
    seen: set[tuple[Any, Any]] = set()
    out: list[dict[str, Any]] = []
    for lst in lists:
        if not lst:
            continue
        for action in lst:
            if not isinstance(action, dict):
                continue
            path = action.get("path")
            path_key: Any
            if isinstance(path, (list, tuple)):
                path_key = tuple(path)
            else:
                path_key = path
            key = (
                action.get("alias") or action.get("tool") or path_key,
                action.get("label"),
            )
            if key in seen:
                continue
            seen.add(key)
            out.append(dict(action))
    return out


def build_assistant_actions(session_ctx: Any) -> list[dict[str, Any]]:
    """Map ``next_commands`` to human-readable progressive-disclosure actions."""
    from palm.services.assist.registry import scenario_by_id

    session_id = str(session_ctx.session_id)
    scenario_id = session_ctx.scenario_id
    handoff_alias: str | None = None
    if scenario_id:
        contributor = scenario_by_id(scenario_id)
        if contributor:
            for alias, target in contributor.mcp_aliases:
                if target and target[-1] == "handoff":
                    handoff_alias = alias
                    break

    actions: list[dict[str, Any]] = []
    for path in session_ctx.next_commands:
        if not path or path[0] != "assist" or len(path) < 3 or path[1] != "session":
            continue
        verb = path[-1] if len(path) > 3 else None
        if verb == "handoff" and handoff_alias:
            actions.append(
                {
                    "label": VERB_ACTION_LABELS["handoff"],
                    "alias": handoff_alias,
                    "params": {"session_id": session_id},
                }
            )
            continue
        if verb in VERB_ACTION_LABELS:
            label = VERB_ACTION_LABELS[verb]
        elif len(path) == 3 and path[1] == "session":
            label = "Inspect session"
        else:
            label = verb.replace("_", " ").title() if verb else "Continue"
        actions.append({"label": label, "path": list(path)})

    invoke_tree = session_ctx.invoke_tree
    if isinstance(invoke_tree, dict):
        active_child = invoke_tree.get("active_child")
        if isinstance(active_child, dict):
            child_id = active_child.get("instance_id")
            if child_id:
                actions.append(
                    {
                        "label": "Open child session",
                        "path": ["flows", "session", str(child_id)],
                    }
                )

    return actions


__all__ = [
    "VERB_ACTION_LABELS",
    "build_assistant_actions",
    "default_turn_actions",
    "merge_assistant_actions",
    "resource_assistant_actions",
]
