"""Assist session read models — enriched operator views."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from palm.core.orchestration import JobStatus
from palm.services.assist.grammar import command_path


@dataclass
class AssistSessionContext:
    """Assist-oriented session view with operator hints and handoff readiness."""

    session_id: str
    scenario_id: str | None = None
    flow_id: str | None = None
    job_id: str | None = None
    status: str = ""
    pattern: str | None = None
    waiting_for_input: bool = False
    handoff_ready: bool = False
    operator_hint: str | None = None
    compose_status: dict[str, Any] | None = None
    next_commands: list[list[str]] = field(default_factory=list)
    detail: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "session_id": self.session_id,
            "scenario_id": self.scenario_id,
            "flow_id": self.flow_id,
            "job_id": self.job_id,
            "status": self.status,
            "pattern": self.pattern,
            "waiting_for_input": self.waiting_for_input,
            "handoff_ready": self.handoff_ready,
            "next_commands": self.next_commands,
            "detail": self.detail,
        }
        if self.operator_hint is not None:
            payload["operator_hint"] = self.operator_hint
        if self.compose_status is not None:
            payload["compose_status"] = self.compose_status
        return payload


def build_assist_session_context(
    *,
    session_id: str,
    flow_id: str | None,
    view: dict[str, Any],
    scenario_id: str | None = None,
    operator_hint: str | None = None,
    compose_status: dict[str, Any] | None = None,
    handoff_ready: bool = False,
) -> AssistSessionContext:
    status = str(view.get("status") or "")
    waiting = status == JobStatus.WAITING_FOR_INPUT.value
    ctx = AssistSessionContext(
        session_id=session_id,
        scenario_id=scenario_id,
        flow_id=flow_id or _flow_name(view),
        job_id=_optional_str(view.get("job_id")),
        status=status,
        pattern=_pattern_name(view),
        waiting_for_input=waiting,
        handoff_ready=handoff_ready,
        operator_hint=operator_hint,
        compose_status=compose_status,
        detail=dict(view),
    )
    ctx.next_commands = _next_commands(ctx)
    return ctx


def _next_commands(ctx: AssistSessionContext) -> list[list[str]]:
    session_id = ctx.session_id
    commands: list[list[str]] = [
        command_path(session_id=session_id),
    ]
    if ctx.waiting_for_input:
        commands.append(command_path(session_id=session_id, verb="input"))
        commands.append(command_path(session_id=session_id, verb="backtrack"))
    if ctx.status == JobStatus.WAITING_FOR_INPUT.value:
        commands.append(command_path(session_id=session_id, verb="resume"))
    if ctx.handoff_ready or ctx.status == JobStatus.SUCCEEDED.value:
        commands.append(command_path(session_id=session_id, verb="handoff"))
    commands.append(command_path(session_id=session_id, verb="cancel"))
    return commands


def _pattern_name(view: dict[str, Any]) -> str | None:
    pattern = view.get("pattern")
    if isinstance(pattern, str):
        return pattern
    if isinstance(pattern, dict):
        name = pattern.get("pattern")
        return str(name) if name is not None else None
    return None


def _flow_name(view: dict[str, Any]) -> str | None:
    for key in ("flow_name", "flow"):
        value = view.get(key)
        if value is not None:
            return str(value)
    pattern = view.get("pattern")
    if isinstance(pattern, dict):
        flow = pattern.get("flow")
        if flow is not None:
            return str(flow)
    return None


def _optional_str(value: object | None) -> str | None:
    return str(value) if value is not None else None


__all__ = ["AssistSessionContext", "build_assist_session_context"]