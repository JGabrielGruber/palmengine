"""
Operator input coercion — plain strings to wizard/job Python values.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any


def coerce_job_input(raw: str, pattern: Mapping[str, Any]) -> Any:
    """Coerce a posted operator input string to the expected Python value."""
    field_type = pattern.get("field_type")
    schema_type = pattern.get("effective_schema_type")

    if field_type == "choice":
        return raw
    if field_type == "confirm":
        return raw.lower() in {"true", "1", "yes", "on"}
    if schema_type == "integer":
        return int(raw)
    if schema_type == "number":
        return float(raw)
    if schema_type == "boolean":
        return raw.lower() in {"true", "1", "yes", "on"}

    choices = pattern.get("choices")
    if isinstance(choices, list) and raw in [str(item) for item in choices]:
        return raw

    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return raw


def pattern_from_wizard_view(wizard_view: Mapping[str, Any]) -> dict[str, Any]:
    """Build a coercion pattern dict from a wizard read model."""
    prompt = wizard_view.get("prompt") or {}
    return {
        "field_type": prompt.get("field_type"),
        "effective_schema_type": prompt.get("effective_schema_type"),
        "choices": prompt.get("choices"),
    }


def pattern_from_job_context(job_context: Mapping[str, Any]) -> dict[str, Any]:
    """Build a coercion pattern dict from a job context read model."""
    pattern = job_context.get("pattern")
    if isinstance(pattern, dict):
        return {
            "field_type": pattern.get("field_type"),
            "effective_schema_type": pattern.get("effective_schema_type"),
            "choices": pattern.get("choices"),
        }
    prompt = job_context.get("prompt") or {}
    return {
        "field_type": prompt.get("field_type"),
        "effective_schema_type": prompt.get("effective_schema_type"),
        "choices": prompt.get("choices"),
    }


def resolve_mcp_wizard_input(
    *,
    input: str | None,
    value: Any | None,
    wizard_view: Mapping[str, Any],
) -> Any:
    """Resolve MCP wizard input — prefer plain ``input`` strings over structured JSON."""
    if input is None and value is None:
        raise ValueError("provide input (plain string) or value")

    raw = input if input is not None else value
    if isinstance(raw, str):
        stripped = raw.strip()
        prompt = wizard_view.get("prompt") or {}
        if prompt.get("collection_phase") or prompt.get("step_kind") == "collection":
            from palm.common.operator.collection_input import resolve_wizard_collection_action

            resolved = resolve_wizard_collection_action(
                stripped,
                value=value if input is None else None,
                wizard_view=wizard_view,
            )
            if isinstance(resolved, tuple):
                return resolved
            raw = resolved
        return coerce_job_input(str(raw), pattern_from_wizard_view(wizard_view))
    return raw


def resolve_mcp_job_input(
    *,
    input: str | None,
    value: Any | None,
    job_context: Mapping[str, Any],
) -> Any:
    """Resolve MCP job input — prefer plain ``input`` strings over structured JSON."""
    if input is None and value is None:
        raise ValueError("provide input (plain string) or value")

    raw = input if input is not None else value
    if isinstance(raw, str):
        return coerce_job_input(raw, pattern_from_job_context(job_context))
    return raw


__all__ = [
    "coerce_job_input",
    "pattern_from_job_context",
    "pattern_from_wizard_view",
    "resolve_mcp_job_input",
    "resolve_mcp_wizard_input",
]