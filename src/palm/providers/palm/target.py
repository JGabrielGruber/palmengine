"""Parse Palm provider invoke targets from resource ids and params."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PalmInvokeTarget:
    """Resolved compositional invoke target."""

    kind: str
    ref: str
    by_id: bool = False


def parse_target(
    *,
    action: str,
    resource_id: str | None,
    params: dict[str, Any],
) -> PalmInvokeTarget:
    """Resolve target kind and reference from action, id, and params."""
    by_id = bool(params.get("by_id", False))

    explicit_kind = params.get("target_kind") or params.get("kind")
    explicit_ref = (
        params.get("target")
        or params.get("flow_name")
        or params.get("process_name")
        or params.get("resource_ref")
        or params.get("name")
    )

    if explicit_kind and explicit_ref:
        return PalmInvokeTarget(kind=str(explicit_kind), ref=str(explicit_ref), by_id=by_id)

    if resource_id:
        text = str(resource_id).strip()
        if ":" in text:
            kind, ref = text.split(":", 1)
            return PalmInvokeTarget(kind=kind.strip(), ref=ref.strip(), by_id=by_id)
        default_kind = _default_kind_for_action(action)
        return PalmInvokeTarget(kind=default_kind, ref=text, by_id=by_id)

    if explicit_ref:
        return PalmInvokeTarget(
            kind=str(explicit_kind or _default_kind_for_action(action)),
            ref=str(explicit_ref),
            by_id=by_id,
        )

    raise ValueError(f"Palm invoke requires resource_id or target params for action {action!r}")


def _default_kind_for_action(action: str) -> str:
    if action == "submit_process":
        return "process"
    if action == "invoke_resource":
        return "resource"
    if action == "fetch":
        return "job"
    return "flow"
