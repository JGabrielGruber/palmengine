"""Design proposal envelope parsing — shared body normalization helpers."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

class PublishAction(str, Enum):
    """How ``commit_proposal`` should publish a validated proposal."""

    CREATE = "create"
    UPDATE = "update"


@dataclass(frozen=True)
class PublishIntent:
    """Resolved publish action for a design proposal."""

    action: PublishAction
    flow_id: str


def extract_flow_dict(body: dict[str, Any]) -> dict[str, Any] | None:
    """Return the inner flow dict from a proposal envelope, if present."""
    flow_section = body.get("flow")
    if isinstance(flow_section, dict):
        return flow_section
    if "pattern" in body or "name" in body or "flow_name" in body:
        return body
    return None


def resolve_flow_id_from_body(body: dict[str, Any], *, base_flow_id: str | None = None) -> str | None:
    """Best-effort flow id from a proposal payload."""
    if base_flow_id:
        return str(base_flow_id)
    flow_section = body.get("flow")
    if isinstance(flow_section, dict):
        for key in ("definition_id", "id", "name"):
            value = flow_section.get(key)
            if value:
                return str(value)
    for key in ("definition_id", "flow_id", "flow_name", "name"):
        value = body.get(key)
        if value:
            return str(value)
    return None


def validation_body(body: dict[str, Any]) -> dict[str, Any]:
    """Normalize proposal payload for ``validate_flow`` (expects ``flow`` wrapper)."""
    if "flow" in body or "wizard" in body or "flow_name" in body:
        return body
    return {"flow": body}


def resolve_publish_intent(
    *,
    body: dict[str, Any],
    base_flow_id: str | None,
    flow_id: str | None,
    flow_exists: Callable[[str], bool],
) -> PublishIntent | None:
    """Resolve whether commit should create or update a catalog flow."""
    resolved = flow_id or resolve_flow_id_from_body(body, base_flow_id=base_flow_id)
    if not resolved:
        return None
    if base_flow_id:
        return PublishIntent(PublishAction.UPDATE, str(base_flow_id))
    if flow_exists(resolved):
        return PublishIntent(PublishAction.UPDATE, resolved)
    return PublishIntent(PublishAction.CREATE, resolved)


__all__ = [
    "PublishAction",
    "PublishIntent",
    "extract_flow_dict",
    "resolve_flow_id_from_body",
    "resolve_publish_intent",
    "validation_body",
]