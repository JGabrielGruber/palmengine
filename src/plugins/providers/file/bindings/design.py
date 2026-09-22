"""File document provider design proposal validation (0.28.1+ provider)."""

from __future__ import annotations

from typing import Any

from palm.common.resource.design_validation import validate_file_resource


def validate_file_design_proposal(body: dict[str, Any], _context: Any) -> tuple[bool, list[str]]:
    """Validate resource proposals targeting the ``file`` document provider."""
    from palm.services.definitions.parsers import parse_resource
    from palm.services.design.envelope import extract_resource_dict

    payload = extract_resource_dict(body)
    if payload is None:
        return True, []
    if str(payload.get("provider") or "") != "file":
        return True, []

    try:
        resource = parse_resource(payload)
    except (TypeError, ValueError, KeyError) as exc:
        return False, [str(exc)]

    blockers = validate_file_resource(resource)
    return (not blockers, blockers)


def register_file_design_contributor() -> None:
    from palm.services.design.registry import DesignContributor, register_design_contributor

    register_design_contributor(
        DesignContributor(
            contributor_id="file",
            validate=validate_file_design_proposal,
            summary="File document resource path and action validation",
        ),
    )


__all__ = ["register_file_design_contributor", "validate_file_design_proposal"]