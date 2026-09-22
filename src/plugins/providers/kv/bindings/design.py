"""KV provider design proposal validation."""

from __future__ import annotations

from typing import Any

from palm.common.resource.design_validation import validate_kv_resource


def validate_kv_design_proposal(body: dict[str, Any], _context: Any) -> tuple[bool, list[str]]:
    """Validate resource proposals targeting the ``kv`` provider."""
    from palm.services.definitions.parsers import parse_resource
    from palm.services.design.envelope import extract_resource_dict

    payload = extract_resource_dict(body)
    if payload is None:
        return True, []
    if str(payload.get("provider") or "") != "kv":
        return True, []

    try:
        resource = parse_resource(payload)
    except (TypeError, ValueError, KeyError) as exc:
        return False, [str(exc)]

    blockers = validate_kv_resource(resource)
    return (not blockers, blockers)


def register_kv_design_contributor() -> None:
    from palm.services.design.registry import DesignContributor, register_design_contributor

    register_design_contributor(
        DesignContributor(
            contributor_id="kv",
            validate=validate_kv_design_proposal,
            summary="KV resource action, backend, and namespace validation",
        ),
    )


__all__ = ["register_kv_design_contributor", "validate_kv_design_proposal"]