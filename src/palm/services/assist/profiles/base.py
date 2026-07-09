"""Assist render profiles — tool (MCP) vs chat (Portal/WS)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class AssistProfile(str, Enum):
    """Presentation + policy profile for a dispatch turn."""

    TOOL = "tool"
    CHAT = "chat"


@dataclass(frozen=True, slots=True)
class RenderOptions:
    """How to present an assist/domain result."""

    profile: AssistProfile = AssistProfile.TOOL
    view_format: str = "assistant"
    include_input_schema: bool = False
    # Chat-only continuity (WS may still apply until fully migrated)
    auto_start: bool = True
    auto_continue_intro: bool = True
    filter_agent_actions: bool = False

    @classmethod
    def for_tool(cls, **overrides: Any) -> RenderOptions:
        base = {
            "profile": AssistProfile.TOOL,
            "include_input_schema": False,
            "filter_agent_actions": False,
            "auto_start": False,
            "auto_continue_intro": False,
        }
        base.update(overrides)
        return cls(**base)

    @classmethod
    def for_chat(cls, **overrides: Any) -> RenderOptions:
        base = {
            "profile": AssistProfile.CHAT,
            "include_input_schema": True,
            "filter_agent_actions": True,
            "auto_start": True,
            "auto_continue_intro": True,
        }
        base.update(overrides)
        return cls(**base)


def resolve_profile(params: dict[str, Any] | None) -> AssistProfile:
    """Explicit ``profile`` param, else infer from include_input_schema."""
    if not params:
        return AssistProfile.TOOL
    raw = params.get("profile")
    if raw is not None:
        text = str(raw).strip().lower()
        if text in {"chat", "human", "portal", "ws"}:
            return AssistProfile.CHAT
        if text in {"tool", "agent", "mcp"}:
            return AssistProfile.TOOL
    from palm.services.assist._params import want_input_schema

    if want_input_schema(params):
        return AssistProfile.CHAT
    return AssistProfile.TOOL


def render_options_from_params(params: dict[str, Any] | None) -> RenderOptions:
    profile = resolve_profile(params)
    if profile is AssistProfile.CHAT:
        opts = RenderOptions.for_chat()
    else:
        opts = RenderOptions.for_tool()
    if not params:
        return opts
    # Allow explicit overrides
    kwargs: dict[str, Any] = {"profile": profile}
    if "include_input_schema" in params:
        from palm.services.assist._params import want_input_schema

        kwargs["include_input_schema"] = want_input_schema(params)
    for key in ("auto_start", "auto_continue_intro", "filter_agent_actions"):
        if key in params:
            kwargs[key] = bool(params[key])
    return RenderOptions(
        profile=kwargs.get("profile", opts.profile),
        view_format=opts.view_format,
        include_input_schema=kwargs.get("include_input_schema", opts.include_input_schema),
        auto_start=kwargs.get("auto_start", opts.auto_start),
        auto_continue_intro=kwargs.get("auto_continue_intro", opts.auto_continue_intro),
        filter_agent_actions=kwargs.get("filter_agent_actions", opts.filter_agent_actions),
    )


__all__ = [
    "AssistProfile",
    "RenderOptions",
    "render_options_from_params",
    "resolve_profile",
]
