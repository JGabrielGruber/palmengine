"""Tool profile — MCP / agents: lean turns, full progressive actions."""

from __future__ import annotations

from typing import Any

from palm.services.assist.profiles.base import AssistProfile, RenderOptions


def tool_render_options(**overrides: Any) -> RenderOptions:
    return RenderOptions.for_tool(**overrides)


def apply_tool_action_policy(payload: dict[str, Any]) -> dict[str, Any]:
    """Tool profile keeps agent-oriented actions as shaped by present/."""
    return payload


PROFILE = AssistProfile.TOOL

__all__ = ["PROFILE", "apply_tool_action_policy", "tool_render_options"]
