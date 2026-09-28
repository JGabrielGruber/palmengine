"""Compat re-exports — implementation lives in ``services.assist.present``."""

from __future__ import annotations

from services.assist.present import (
    DESIGN_DISCOVERY_INTENTS,
    build_assistant_actions,
    build_assistant_view,
    design_discovery_actions,
    design_discovery_hint,
    ensure_assist_view_registration,
    merge_assistant_actions,
    post_terminal_design_actions,
    prioritize_assistant_actions_for_design,
    resolve_view_format,
)

__all__ = [
    "DESIGN_DISCOVERY_INTENTS",
    "build_assistant_actions",
    "build_assistant_view",
    "design_discovery_actions",
    "design_discovery_hint",
    "ensure_assist_view_registration",
    "merge_assistant_actions",
    "post_terminal_design_actions",
    "prioritize_assistant_actions_for_design",
    "resolve_view_format",
]
