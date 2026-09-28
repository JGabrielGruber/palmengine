"""Assistant view pipeline entry — compose + humanize + actions."""

from __future__ import annotations

from typing import Any

from palm.common.operator.compact import compact_wizard_inspect
from palm.common.operator.compose_status import build_compose_status
from palm.common.operator.view_registry import OperatorViewContext
from services.assist.present.actions import default_turn_actions
from services.assist.present.flatten import (
    flatten_view,
    invoke_tree_from_snapshot,
    merge_snapshot_fields,
)
from services.assist.present.humanize import humanize_assistant_view
from services.assist.registry import apply_assistant_enricher


def build_assistant_view(
    flat_view: dict[str, Any],
    *,
    context: OperatorViewContext,
) -> dict[str, Any]:
    """Build a human-first assistant turn from a flattened session inspect view."""
    flat = flatten_view(flat_view)
    snapshot = compact_wizard_inspect(
        flat,
        include_operator_hint=False,
        stored_mutation_gate=context.stored_mutation_gate,
    )
    invoke_tree = context.invoke_tree or invoke_tree_from_snapshot(snapshot)
    composed = build_compose_status(invoke_tree, snapshot)
    merge_snapshot_fields(composed, snapshot)
    payload = humanize_assistant_view(composed, context=context)
    # Compact pipeline drops non-wizard keys; re-apply system session (0.58.9).
    # session_id = system subject only; instance_id = continue handle.
    system_sid = flat_view.get("session_id") or flat.get("session_id")
    instance_id = (
        flat_view.get("instance_id")
        or flat.get("instance_id")
        or context.session_id
    )
    if instance_id is not None and str(instance_id).strip():
        payload["instance_id"] = str(instance_id).strip()
    if (
        system_sid is not None
        and str(system_sid).strip()
        and str(system_sid).startswith("sess-")
    ):
        sid = str(system_sid).strip()
        payload["session_id"] = sid
        refs = payload.get("refs")
        if not isinstance(refs, dict):
            refs = {}
        refs["session_id"] = sid
        if payload.get("instance_id"):
            refs.setdefault("instance_id", payload["instance_id"])
        payload["refs"] = refs
    elif payload.get("session_id") and not str(payload["session_id"]).startswith("sess-"):
        # Drop product-instance masquerading as session_id on the envelope.
        payload.pop("session_id", None)
    scenario_id = context.scenario_id
    if scenario_id:
        payload = apply_assistant_enricher(scenario_id, payload, context=context)
    from palm.common.operator.collection_actions import build_collection_assistant_actions

    session_id = str(
        context.session_id
        or payload.get("session_id")
        or composed.get("instance_id")
        or ""
    )
    collection_actions = build_collection_assistant_actions(
        composed,
        session_id=session_id,
        flow_id=context.flow_id,
    )
    if collection_actions:
        payload["actions"] = collection_actions
    if not payload.get("actions"):
        default_actions = default_turn_actions(
            payload,
            composed,
            session_id=session_id or None,
            flow_id=context.flow_id,
        )
        if default_actions:
            payload["actions"] = default_actions
    return payload


__all__ = ["build_assistant_view"]
