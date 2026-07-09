"""View format resolution and operator registry registration."""

from __future__ import annotations

from typing import Any


def resolve_view_format(params: dict[str, Any] | None, *, default: str = "assistant") -> str:
    """Read ``format`` from dispatch/REST params with canonical normalization."""
    from palm.common.operator.view_registry import normalize_view_format

    if not params:
        return normalize_view_format(default)
    raw = params.get("format", default)
    return normalize_view_format(str(raw))


def ensure_assist_view_registration() -> None:
    """Register the assistant view builder with the operator view registry."""
    from palm.common.operator.view_registry import register_operator_view_builder
    from palm.services.assist.present.pipeline import build_assistant_view

    register_operator_view_builder("assistant", build_assistant_view)


__all__ = ["ensure_assist_view_registration", "resolve_view_format"]
