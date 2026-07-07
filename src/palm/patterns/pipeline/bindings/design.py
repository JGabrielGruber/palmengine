"""Pipeline design proposal validation — registered via pattern ``design_contributor`` hook."""

from __future__ import annotations

from typing import Any

from palm.common.exceptions import DefinitionBuildError


def register_pipeline_design_contributor() -> None:
    """Register pipeline-specific design proposal checks at pattern bootstrap."""
    from palm.services.design.registry import DesignContributor, register_design_contributor

    register_design_contributor(
        DesignContributor(
            contributor_id="pipeline",
            validate=validate_pipeline_design_proposal,
            summary="Pipeline transform step integrity and options sanity",
        )
    )


def validate_pipeline_design_proposal(body: dict[str, Any], _context: Any) -> tuple[bool, list[str]]:
    """Validate pipeline flow payloads inside a design proposal envelope."""
    from palm.services.design.envelope import extract_flow_dict

    flow = extract_flow_dict(body)
    if flow is None or str(flow.get("pattern") or "") != "pipeline":
        return True, []

    blockers: list[str] = []
    options = flow.get("options")
    if not isinstance(options, dict):
        return False, ["pipeline flow requires an options object"]

    steps_raw = options.get("steps")
    if not isinstance(steps_raw, list) or not steps_raw:
        blockers.append("Pipeline requires a non-empty 'steps' list")
        return (False, blockers)

    seen_names: set[str] = set()
    parsed_count = 0
    for index, raw_step in enumerate(steps_raw):
        if not isinstance(raw_step, dict):
            blockers.append(f"pipeline step[{index}] must be an object")
            continue
        try:
            from palm.common.transforms.builder import transform_step_from_mapping

            spec = transform_step_from_mapping(raw_step)
        except DefinitionBuildError as exc:
            blockers.append(str(exc))
            continue
        parsed_count += 1
        if spec.name in seen_names:
            blockers.append(f"duplicate pipeline step name: {spec.name!r}")
        seen_names.add(spec.name)

    if parsed_count == 0 and not blockers:
        blockers.append("Pipeline 'steps' must contain step dicts")

    return (not blockers, blockers)


__all__ = [
    "register_pipeline_design_contributor",
    "validate_pipeline_design_proposal",
]