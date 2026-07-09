"""Assist presentation pipeline — shared by tool and chat profiles."""

from palm.services.assist.present.actions import (
    build_assistant_actions,
    merge_assistant_actions,
)
from palm.services.assist.present.design_actions import (
    DESIGN_DISCOVERY_INTENTS,
    design_discovery_actions,
    design_discovery_hint,
    post_terminal_design_actions,
    prioritize_assistant_actions_for_design,
)
from palm.services.assist.present.format import (
    ensure_assist_view_registration,
    resolve_view_format,
)
from palm.services.assist.present.pipeline import build_assistant_view

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
