"""Assist MCP tools — stable ``palm_assist`` parametric dispatch proxy."""

from __future__ import annotations

from typing import Any

from palm.common.services.errors import DefinitionNotFoundServiceError
from palm.runtimes.mcp.assist.dispatch import (
    compact_dispatch_result,
    resolve_dispatch_path,
)
from palm.runtimes.mcp.rest_client import PalmRestError


def register_assist_tools(mcp: Any, backend: Any) -> None:
    """Register the stable ``palm_assist`` operator dispatch tool."""

    @mcp.tool
    def palm_assist(
        path: list[str] | None = None,
        alias: str | None = None,
        params: dict[str, Any] | None = None,
        action: str = "dispatch",
    ) -> dict[str, Any]:
        """Dispatch a service command path (assist, flows, processes, …).

        Prefer ``path`` or ``alias`` with optional ``params``. Returns a compact
        operator view. Example::

            palm_assist(path=["assist", "scenarios", "operator-entry", "start"])
            palm_assist(alias="operator-entry/start")
        """
        if action != "dispatch":
            raise ValueError(f"unsupported palm_assist action: {action!r}")
        try:
            resolved = resolve_dispatch_path(path=path, alias=alias, params=params)
            result = backend.assist_dispatch(resolved, params=params or {})
        except (TypeError, ValueError, DefinitionNotFoundServiceError) as exc:
            raise ValueError(str(exc)) from exc
        except PalmRestError as exc:
            raise ValueError(str(exc)) from exc
        return compact_dispatch_result(resolved, result)


__all__ = ["register_assist_tools"]