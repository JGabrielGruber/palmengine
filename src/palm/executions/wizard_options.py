"""
Wizard-specific flow options — metadata parsing for definitions and repository.
"""

from __future__ import annotations

from typing import Any

from palm.executions.exceptions import DefinitionBuildError


def parse_wizard_flow_options(options: dict[str, Any]) -> dict[str, Any]:
    """
    Normalize wizard keys from a ``FlowDefinition.options`` payload.

    Returns a dict suitable for ``wizard_config_from_options`` plus build metadata.
    """
    normalized = dict(options)
    normalized.setdefault("allow_backtrack", options.get("allow_backtrack", True))
    normalized["include_summary"] = bool(options.get("include_summary", False))
    normalized["include_commit"] = bool(options.get("include_commit", False))

    commit_hook = options.get("commit_hook")
    if commit_hook is not None:
        normalized["commit_hook"] = str(commit_hook)

    intro = options.get("introduction_slug")
    if intro is not None:
        normalized["introduction_slug"] = str(intro)

    if "steps" in options and isinstance(options["steps"], list):
        normalized["steps"] = [_normalize_step_dict(item) for item in options["steps"]]

    return normalized


def wizard_metadata_from_flow(options: dict[str, Any]) -> dict[str, Any]:
    """Extract non-config wizard metadata stored on job definitions."""
    meta: dict[str, Any] = {}
    if options.get("commit_hook"):
        meta["commit_hook"] = str(options["commit_hook"])
    if options.get("include_summary"):
        meta["include_summary"] = True
    if options.get("include_commit"):
        meta["include_commit"] = True
    if options.get("resource_provider"):
        meta["resource_provider"] = str(options["resource_provider"])
    return meta


def _normalize_step_dict(item: Any) -> Any:
    if not isinstance(item, dict):
        return item
    step = dict(item)
    validation = step.get("validation")
    if isinstance(validation, list):
        step["validation"] = [_normalize_rule(rule) for rule in validation]
    return step


def _normalize_rule(rule: Any) -> dict[str, Any]:
    if isinstance(rule, dict) and "rule" in rule:
        return {"rule": str(rule["rule"]), "params": dict(rule.get("params") or {})}
    if isinstance(rule, str):
        return {"rule": rule, "params": {}}
    raise DefinitionBuildError(f"Invalid validation rule: {rule!r}")