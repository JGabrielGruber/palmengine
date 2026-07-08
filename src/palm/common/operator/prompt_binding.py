"""Wizard prompt template binding — ``{{ state.key }}`` interpolation for human copy."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from palm.core.resource.invocation import bind_resource_value


def resolve_wizard_prompt(text: str | None, binding: Mapping[str, Any] | None) -> str | None:
    """
    Interpolate ``{{ state.path }}`` placeholders in wizard ``prompt`` / ``title`` strings.

    Uses the same binding rules as resource params: the segment after ``state.`` resolves
    against flat keys in ``binding`` (typically wizard answers).
    """
    if text is None:
        return None
    if not binding:
        return text
    result = bind_resource_value(text, binding)
    return str(result) if isinstance(result, str) else text


__all__ = ["resolve_wizard_prompt"]