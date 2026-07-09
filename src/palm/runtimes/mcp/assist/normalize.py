"""Normalize and resolve palm_assist path / alias / params."""

from __future__ import annotations

from typing import Any

from palm.services.assist.registry import resolve_mcp_alias
from palm.services.design.registry import resolve_design_mcp_alias

_DEFAULT_ASSIST_ALIAS = "operator-entry/start"


def clean_dispatch_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def looks_like_design_publish_body(params: dict[str, Any]) -> bool:
    """True when params carry a flow/resource definition body for one-shot publish."""
    body = params.get("body")
    if not isinstance(body, dict) or not body:
        if params.get("name") and (params.get("pattern") or params.get("options")):
            return True
        if params.get("name") and params.get("provider"):
            return True
        return False
    if body.get("name") or body.get("pattern") or body.get("options"):
        return True
    if body.get("provider") or body.get("resource_id"):
        return True
    return False


def normalize_assist_dispatch_args(
    *,
    path: list[str] | None = None,
    alias: str | None = None,
    params: dict[str, Any] | None = None,
) -> tuple[list[str] | None, str | None, dict[str, Any], bool]:
    """Coerce weak-LLM tool payloads and apply human-first defaults.

    Returns ``(path, alias, params, used_default_entry)``.
    """
    params = dict(params or {})
    used_default_entry = False

    alias = clean_dispatch_str(alias)
    if alias is None:
        alias = clean_dispatch_str(params.pop("alias", None))

    if path is not None:
        cleaned = [clean_dispatch_str(segment) for segment in path]
        path = [segment for segment in cleaned if segment] or None
    if path is None:
        nested = params.pop("path", None)
        if isinstance(nested, list):
            cleaned = [clean_dispatch_str(segment) for segment in nested]
            path = [segment for segment in cleaned if segment] or None

    if not alias and not path:
        session_id = clean_dispatch_str(params.get("session_id")) or clean_dispatch_str(
            params.get("instance_id")
        )
        flow_id = clean_dispatch_str(params.get("flow_id"))
        has_value = "value" in params or "input" in params
        collection_action = params.get("collection_action")
        edit = params.get("edit")
        if session_id and flow_id and (
            has_value or collection_action is not None or isinstance(edit, dict)
        ):
            path = ["flows", flow_id, "session", session_id, "input"]
            if collection_action is not None and "input" not in params:
                action_text = clean_dispatch_str(collection_action) or str(collection_action)
                params["input"] = action_text
        elif session_id and has_value:
            path = ["assist", "session", session_id, "input"]
        elif session_id and flow_id:
            path = ["flows", flow_id, "session", session_id]
        elif session_id:
            path = ["assist", "session", session_id]
        elif flow_id:
            path = ["flows", flow_id, "create"]
        else:
            scenario_id = clean_dispatch_str(params.get("scenario_id"))
            if scenario_id:
                alias = f"{scenario_id}/start"
            elif looks_like_design_publish_body(params):
                kind = clean_dispatch_str(params.get("kind")) or "flow"
                if kind in {"resource", "publish-resource"}:
                    alias = "design/publish-resource"
                else:
                    alias = "design/publish"

    if not alias and not path:
        alias = _DEFAULT_ASSIST_ALIAS
        used_default_entry = True

    return path, alias, params, used_default_entry


def resolve_dispatch_path(
    *,
    path: list[str] | None = None,
    alias: str | None = None,
    params: dict[str, Any] | None = None,
) -> list[str]:
    """Resolve alias or explicit path into a concrete command path."""
    path, alias, params, _ = normalize_assist_dispatch_args(
        path=path,
        alias=alias,
        params=params,
    )
    if alias:
        resolved = resolve_mcp_alias(alias, params=params)
        if resolved is None:
            resolved = resolve_design_mcp_alias(alias, params=params)
        if resolved is None:
            if alias == _DEFAULT_ASSIST_ALIAS:
                return ["assist", "scenarios"]
            raise ValueError(f"unknown MCP alias: {alias!r}")
        return list(resolved)
    if path:
        return [str(segment) for segment in path]
    return ["assist", "scenarios"]


__all__ = [
    "clean_dispatch_str",
    "looks_like_design_publish_body",
    "normalize_assist_dispatch_args",
    "resolve_dispatch_path",
]
