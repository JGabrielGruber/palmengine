"""Wizard design proposal validation — registered via pattern ``design_contributor`` hook."""

from __future__ import annotations

from typing import Any

from palm.common.exceptions import DefinitionBuildError
from palm.patterns.wizard.bindings.definitions.builder import wizard_config_from_options
from palm.patterns.wizard.bindings.definitions.options import parse_wizard_flow_options
def register_wizard_design_contributor() -> None:
    """Register wizard-specific design proposal checks at pattern bootstrap."""
    from palm.services.design.registry import DesignContributor, register_design_contributor

    register_design_contributor(
        DesignContributor(
            contributor_id="wizard",
            validate=validate_wizard_design_proposal,
            summary="Wizard step slug integrity, collection fields, and config sanity",
        )
    )


def validate_wizard_design_proposal(body: dict[str, Any], _context: Any) -> tuple[bool, list[str]]:
    """Validate wizard flow payloads inside a design proposal envelope."""
    from palm.services.design.envelope import extract_flow_dict

    flow = extract_flow_dict(body)
    if flow is None or str(flow.get("pattern") or "") != "wizard":
        return True, []

    blockers: list[str] = []
    options = flow.get("options")
    if not isinstance(options, dict):
        return False, ["wizard flow requires an options object"]

    blockers.extend(_validate_step_list(options))
    if options.get("include_commit") and not options.get("commit_hook"):
        blockers.append("wizard with include_commit requires commit_hook in options")

    try:
        wizard_config_from_options(parse_wizard_flow_options(options))
    except (DefinitionBuildError, ValueError, TypeError, KeyError) as exc:
        blockers.append(str(exc))

    return (not blockers, blockers)


def _validate_step_list(options: dict[str, Any]) -> list[str]:
    """Early checks for step dict lists before full wizard config build."""
    steps = options.get("steps")
    if not isinstance(steps, list) or not steps:
        if "step_count" in options or "config" in options:
            return []
        return ["wizard options require steps (dicts or slugs), step_count, or config"]

    if not isinstance(steps[0], dict):
        return []

    blockers: list[str] = []
    seen_slugs: set[str] = set()
    for index, raw_step in enumerate(steps):
        if not isinstance(raw_step, dict):
            blockers.append(f"wizard step[{index}] must be an object")
            continue
        slug = str(raw_step.get("slug") or "").strip()
        if not slug:
            blockers.append(f"wizard step[{index}] requires a non-empty slug")
            continue
        if slug in seen_slugs:
            blockers.append(f"duplicate wizard step slug: {slug!r}")
        seen_slugs.add(slug)

        step_kind = str(raw_step.get("step_kind") or "input")
        field_type = str(raw_step.get("field_type") or "text")
        if field_type == "choice" and not raw_step.get("choices"):
            blockers.append(f"wizard step {slug!r} with field_type=choice requires choices")

        if step_kind == "collection":
            blockers.extend(_validate_collection_step(slug, raw_step))
        elif step_kind == "resource" and not raw_step.get("resource_ref"):
            blockers.append(f"wizard resource step {slug!r} requires resource_ref")
        elif step_kind == "transform" and not raw_step.get("transform"):
            blockers.append(f"wizard transform step {slug!r} requires transform configuration")

    return blockers


def _validate_collection_step(slug: str, step: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    item_fields = step.get("item_fields")
    if not isinstance(item_fields, list) or not item_fields:
        blockers.append(f"wizard collection step {slug!r} requires non-empty item_fields")
        return blockers

    field_slugs: set[str] = set()
    for index, raw_field in enumerate(item_fields):
        if not isinstance(raw_field, dict):
            blockers.append(f"wizard collection step {slug!r} item_fields[{index}] must be an object")
            continue
        field_slug = str(raw_field.get("slug") or "").strip()
        if not field_slug:
            blockers.append(
                f"wizard collection step {slug!r} item_fields[{index}] requires slug",
            )
            continue
        if field_slug in field_slugs:
            blockers.append(
                f"wizard collection step {slug!r} has duplicate item field slug: {field_slug!r}",
            )
        field_slugs.add(field_slug)
        if str(raw_field.get("field_type") or "text") == "choice" and not raw_field.get("choices"):
            blockers.append(
                f"wizard collection step {slug!r} field {field_slug!r} "
                "with field_type=choice requires choices",
            )
    return blockers


__all__ = [
    "register_wizard_design_contributor",
    "validate_wizard_design_proposal",
]