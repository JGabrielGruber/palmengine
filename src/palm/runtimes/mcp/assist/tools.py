"""Assist MCP tools — stable ``palm_assist`` parametric dispatch proxy."""

from __future__ import annotations

from typing import Any

from palm.common.services.errors import DefinitionNotFoundServiceError
from palm.runtimes.mcp.assist.dispatch import (
    resolve_dispatch_format,
    resolve_dispatch_path,
    shape_dispatch_result,
)
from palm.runtimes.mcp.rest_client import PalmRestError


def register_assist_tools(mcp: Any, backend: Any) -> None:
    """Register the stable ``palm_assist`` operator dispatch tool."""

    @mcp.tool
    def palm_assist(
        path: list[str] | None = None,
        alias: str | None = None,
        params: dict[str, Any] | None = None,
        action: str | None = None,
        format: str | None = None,
    ) -> dict[str, Any]:
        """Dispatch a service command path (assist, flows, processes, …).

        Prefer ``path`` or ``alias`` with optional ``params``. Assist paths default
        to ``format=assistant`` (human compose view); flows/system default to
        powertool. Example::

            palm_assist(path=["assist", "scenarios", "operator-entry", "start"])
            palm_assist(alias="operator-entry/start", format="assistant")
            palm_assist(path=["flows", "onboard", "session", "inst-1"], format="powertool")
        """
        resolved_action = action or "dispatch"
        resolved_format = format or "assistant"
        if resolved_action != "dispatch":
            raise ValueError(f"unsupported palm_assist action: {resolved_action!r}")
        try:
            resolved = resolve_dispatch_path(path=path, alias=alias, params=params)
            dispatch_params = dict(params or {})
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

        return shape_dispatch_result(
            resolved,
            result,
            format=view_format,
            params=dispatch_params,
            invoke_tree=invoke_tree,
        )


__all__ = ["register_assist_tools"]