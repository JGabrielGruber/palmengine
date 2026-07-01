"""Flow execution read models — session-centric schemas."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from palm.core.orchestration import JobStatus
from palm.services.execution.flows.grammar import command_path


@dataclass
class SessionContext:
    """Verbose session read model — command paths, not transport URLs."""

    session_id: str
    flow_id: str | None = None
    job_id: str | None = None
    status: str = ""
    pattern: str | None = None
    waiting_for_input: bool = False
    next_commands: list[list[str]] = field(default_factory=list)
    detail: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "flow_id": self.flow_id,
            "job_id": self.job_id,
            "status": self.status,
            "pattern": self.pattern,
            "waiting_for_input": self.waiting_for_input,
            "next_commands": self.next_commands,
            "detail": self.detail,
        }


def build_session_context(
    *,
    flow_id: str | None,
    session_id: str,
    view: dict[str, Any],
    enricher: Any | None = None,
) -> SessionContext:
    """Normalize an inspect view into a :class:`SessionContext`."""
    status = str(view.get("status") or "")
    pattern = _pattern_name(view)
    waiting = status == JobStatus.WAITING_FOR_INPUT.value
    detail = dict(view)
    if enricher is not None:
        extra = enricher(pattern, view)
        if extra:
            detail = {**detail, **extra}

    ctx = SessionContext(
        session_id=session_id,
        flow_id=flow_id or _flow_name(view),
        job_id=_optional_str(view.get("job_id")),
        status=status,
        pattern=pattern,
        waiting_for_input=waiting,
        detail=detail,
    )
    ctx.next_commands = _next_commands(ctx, view)
    return ctx


def _next_commands(ctx: SessionContext, view: dict[str, Any]) -> list[list[str]]:
    flow_id = ctx.flow_id
    session_id = ctx.session_id
    if flow_id is None:
        return [command_path()]

    commands: list[list[str]] = [
        command_path(flow_id=flow_id),
        command_path(flow_id=flow_id, session_id=session_id),
    ]
    status = ctx.status
    if status == JobStatus.WAITING_FOR_INPUT.value:
        commands.append(command_path(flow_id=flow_id, session_id=session_id, verb="input"))
        if ctx.pattern == "wizard":
            commands.append(
                command_path(flow_id=flow_id, session_id=session_id, verb="backtrack"),
            )
        commands.append(command_path(flow_id=flow_id, session_id=session_id, verb="resume"))
    if view.get("waiting_for_child") or ctx.detail.get("waiting_for_child"):
        commands.append(
            command_path(flow_id=flow_id, session_id=session_id, verb="resume-child-wait"),
        )
    if status not in {
        JobStatus.SUCCEEDED.value,
        JobStatus.FAILED.value,
        JobStatus.CANCELLED.value,
    }:
        commands.append(command_path(flow_id=flow_id, session_id=session_id, verb="cancel"))
    return commands


def _pattern_name(view: dict[str, Any]) -> str | None:
    metadata = view.get("metadata")
    if isinstance(metadata, dict):
        pattern = metadata.get("pattern")
        if pattern is not None:
            return str(pattern)
    pattern = view.get("pattern")
    return str(pattern) if pattern is not None else None


def _flow_name(view: dict[str, Any]) -> str | None:
    metadata = view.get("metadata")
    if isinstance(metadata, dict):
        for key in ("flow", "flow_name", "wizard"):
            value = metadata.get(key)
            if value is not None:
                return str(value)
    for key in ("flow", "flow_name"):
        value = view.get(key)
        if value is not None:
            return str(value)
    return None


def _optional_str(value: object | None) -> str | None:
    return str(value) if value is not None else None


__all__ = ["SessionContext", "build_session_context"]