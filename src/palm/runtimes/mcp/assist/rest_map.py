"""Map assist command paths to REST method / url / body."""

from __future__ import annotations

from typing import Any


def append_format_query(url_path: str, params: dict[str, Any]) -> str:
    fmt = params.get("format")
    if not fmt:
        return url_path
    separator = "&" if "?" in url_path else "?"
    return f"{url_path}{separator}format={fmt}"


def map_dispatch_to_rest(
    path: list[str],
    params: dict[str, Any] | None = None,
) -> tuple[str, str, dict[str, Any] | None, bool]:
    """Map a command path to REST method, url path, body, and auth flag."""
    params = params or {}
    body = dict(params.get("body") or params) or None
    prefix = path[0]

    if prefix == "assist":
        if path == ["assist", "scenarios"]:
            return "GET", "/v1/api/assist/scenarios", None, False
        if len(path) == 2 and path[1] == "scenarios":
            return "GET", "/v1/api/assist/scenarios", None, False
        if len(path) == 2 and path[0] == "assist" and path[1] == "doctor":
            return "GET", "/v1/api/assist/doctor", None, False
        if len(path) == 3 and path[1] == "scenarios":
            return "GET", f"/v1/api/assist/scenarios/{path[2]}", None, False
        if len(path) == 4 and path[1] == "scenarios" and path[3] == "start":
            url = append_format_query(f"/v1/api/assist/scenarios/{path[2]}/start", params)
            return "POST", url, body, True
        if len(path) == 2 and path[1] == "session":
            raise ValueError("session_id required")
        if len(path) == 3 and path[1] == "session":
            url = append_format_query(f"/v1/api/assist/session/{path[2]}", params)
            return "GET", url, None, False
        if len(path) == 4 and path[1] == "session" and path[3] == "input":
            url = append_format_query(f"/v1/api/assist/session/{path[2]}/input", params)
            return "POST", url, {"value": params.get("value", params.get("input"))}, True
        if len(path) == 4 and path[1] == "session" and path[3] == "backtrack":
            url = append_format_query(f"/v1/api/assist/session/{path[2]}/backtrack", params)
            return "POST", url, {"to_step": params.get("to_step")}, True
        if len(path) == 4 and path[1] == "session" and path[3] == "resume":
            url = append_format_query(f"/v1/api/assist/session/{path[2]}/resume", params)
            return "POST", url, None, True
        if len(path) == 4 and path[1] == "session" and path[3] == "cancel":
            return "POST", f"/v1/api/assist/session/{path[2]}/cancel", None, True
        if len(path) == 4 and path[1] == "session" and path[3] == "handoff":
            return "POST", f"/v1/api/assist/session/{path[2]}/handoff", None, False

    if prefix == "flows":
        if path == ["flows"]:
            return "GET", "/v1/api/flows", None, False
        if len(path) == 2:
            return "GET", f"/v1/api/flows/{path[1]}", None, False
        if len(path) == 3 and path[2] == "create":
            return "POST", f"/v1/api/flows/{path[1]}/create", body, True
        if len(path) == 4 and path[2] == "session":
            url = append_format_query(f"/v1/api/flows/{path[1]}/session/{path[3]}", params)
            return "GET", url, None, False
        if len(path) == 5 and path[2] == "session" and path[4] == "input":
            url = append_format_query(
                f"/v1/api/flows/{path[1]}/session/{path[3]}/input",
                params,
            )
            return "POST", url, {"value": params.get("value", params.get("input"))}, True
        if len(path) == 5 and path[2] == "session" and path[4] == "backtrack":
            url = append_format_query(
                f"/v1/api/flows/{path[1]}/session/{path[3]}/backtrack",
                params,
            )
            return "POST", url, {"to_step": params.get("to_step")}, True
        if len(path) == 5 and path[2] == "session" and path[4] == "resume":
            url = append_format_query(
                f"/v1/api/flows/{path[1]}/session/{path[3]}/resume",
                params,
            )
            return "POST", url, None, True
        if len(path) == 5 and path[2] == "session" and path[4] == "resume-child-wait":
            url = append_format_query(
                f"/v1/api/flows/{path[1]}/session/{path[3]}/resume-child-wait",
                params,
            )
            return "POST", url, None, True
        if len(path) == 5 and path[2] == "session" and path[4] == "cancel":
            return "POST", f"/v1/api/flows/{path[1]}/session/{path[3]}/cancel", None, True

    if prefix == "processes":
        if len(path) == 3 and path[2] == "prepare":
            return "POST", f"/v1/api/processes/{path[1]}/prepare", body, True
        if path[-1] == "submit":
            return "POST", "/v1/api/processes/submit", body, True
        if len(path) == 3 and path[2] == "run":
            return "POST", f"/v1/api/processes/{path[1]}/run", body, True

    if prefix == "system" and path == ["system", "doctor"]:
        return "GET", "/v1/api/system/doctor", None, False

    raise ValueError(f"no REST mapping for dispatch path: {'/'.join(path)}")


__all__ = ["map_dispatch_to_rest"]
