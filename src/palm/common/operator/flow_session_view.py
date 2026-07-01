"""Flow session view shaping — shared by REST and MCP operator surfaces."""

from __future__ import annotations

from typing import Any

from palm.common.operator.compact import compact_wizard_inspect
from palm.common.operator.view_registry import (
    OperatorViewContext,
    build_operator_view,
    normalize_view_format,
)


def shape_flow_session_view(
    flat: dict[str, Any],
    *,
    format: str = "powertool",
    session_id: str | None = None,
    flow_id: str | None = None,
    path: list[str] | None = None,
    invoke_tree: dict[str, Any] | None = None,
    include: list[str] | None = None,
    truncate_answers_at: int = 2000,
) -> dict[str, Any]:
    """Shape a flattened flow session inspect view for operator consumers."""
    fmt = normalize_view_format(format or "powertool")
    if fmt == "verbose":
        return dict(flat)
    if fmt == "assistant":
        sid = session_id or flat.get("instance_id") or flat.get("session_id")
        fid = flow_id or flat.get("flow_name") or flat.get("flow")
        context = OperatorViewContext(
            session_id=str(sid) if sid is not None else None,
            flow_id=str(fid) if fid is not None else None,
            scenario_id=None,
            invoke_tree=invoke_tree,
            path=list(path or []),
        )
        return build_operator_view("assistant", flat_view=flat, context=context)
    return compact_wizard_inspect(
        flat,
        format="compact",
        include=include,
        truncate_answers_at=truncate_answers_at,
    )


__all__ = ["shape_flow_session_view"]