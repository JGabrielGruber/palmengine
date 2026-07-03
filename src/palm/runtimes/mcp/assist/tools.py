"""Assist MCP tools — stable ``palm_assist`` parametric dispatch proxy."""

from __future__ import annotations

from typing import Any

from palm.common.services.errors import DefinitionNotFoundServiceError
from palm.runtimes.mcp.assist.dispatch import (
    normalize_assist_dispatch_args,
    resolve_dispatch_format,
    resolve_dispatch_path,
    shape_dispatch_result,
)
from palm.runtimes.mcp.descriptions import tool_description
from palm.runtimes.mcp.rest_client import PalmRestError

_PALM_ASSIST_DESC = tool_description(
    "palm_assist",
    "Primary Palm entry — dispatch assist, flows, and process command paths.",
    when=(
        "Bare ``palm_assist()`` starts operator-entry (0.21.7 default). "
        "Use ``path`` or ``alias`` to target a route; ``params`` carries "
        "``session_id`` + ``value``/``input`` for continuation. Assist paths "
        "default to ``format=assistant``; flows/system default to powertool."
    ),
    examples=[
        "palm_assist()",
        'palm_assist(alias="operator-entry/start")',
        'palm_assist(params={"session_id": "inst-1", "value": "yes"})',
        'palm_assist(path=["flows", "todo-builder", "create"])',
        'palm_assist(params={"session_id": "inst-1", "flow_id": "todo-builder", "value": "yes"})',
    ],
    use_instead=(
        "Prefer ``palm_assist`` over per-domain tools for driving sessions; "
        "use ``palm_flows_create_session`` only when you need the legacy powertool create shape."
    ),
)


def register_assist_tools(mcp: Any, backend: Any) -> None:
    """Register the stable ``palm_assist`` operator dispatch tool."""

    @mcp.tool(description=_PALM_ASSIST_DESC)
    def palm_assist(
        path: list[str] | None = None,
        alias: str | None = None,
        params: dict[str, Any] | None = None,
        action: str | None = None,
        format: str | None = None,
    ) -> dict[str, Any]:
        resolved_action = action or "dispatch"
        resolved_format = format or "assistant"
        if resolved_action != "dispatch":
            raise ValueError(f"unsupported palm_assist action: {resolved_action!r}")
        try:
            norm_path, norm_alias, dispatch_params, used_default_entry = (
                normalize_assist_dispatch_args(path=path, alias=alias, params=params)
            )
            resolved = resolve_dispatch_path(
                path=norm_path,
                alias=norm_alias,
                params=dispatch_params,
            )
            view_format = resolve_dispatch_format(
                resolved,
                params=dispatch_params,
                tool_format=resolved_format,
            )
            if resolved[0] == "assist" and "format" not in dispatch_params:
                dispatch_params["format"] = view_format
            result = backend.assist_dispatch(resolved, params=dispatch_params)
        except (TypeError, ValueError, DefinitionNotFoundServiceError) as exc:
            raise ValueError(str(exc)) from exc
        except PalmRestError as exc:
            raise ValueError(str(exc)) from exc
        invoke_tree = None
        if (
            view_format == "assistant"
            and len(resolved) >= 4
            and resolved[0] == "flows"
            and resolved[2] == "session"
        ):
            invoke_tree = backend.get_instance_tree(resolved[3])

        payload = shape_dispatch_result(
            resolved,
            result,
            format=view_format,
            params=dispatch_params,
            invoke_tree=invoke_tree,
        )
        if used_default_entry:
            payload["dispatch_default"] = "operator-entry/start"
            hint = payload.get("hint") or ""
            suffix = " Started default operator entry (pass alias or path to target elsewhere)."
            payload["hint"] = f"{hint}{suffix}".strip()
        return payload


__all__ = ["register_assist_tools"]