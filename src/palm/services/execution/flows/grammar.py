"""Flow command-path grammar — parse and build REPL-style command chains."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class FlowCommandKind(Enum):
    LIST = "list"
    DESCRIBE = "describe"
    CREATE = "create"
    SESSION = "session"
    SESSION_VERB = "session_verb"


_SESSION_VERBS = frozenset(
    {"input", "backtrack", "resume", "resume-child-wait", "cancel"},
)


@dataclass(frozen=True)
class ParsedFlowCommand:
    kind: FlowCommandKind
    flow_id: str | None = None
    session_id: str | None = None
    verb: str | None = None


def normalize_path(path: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    segments = tuple(str(segment) for segment in path)
    if segments and segments[0] == "flows":
        return segments[1:]
    return segments


def parse_flow_command(path: list[str] | tuple[str, ...]) -> ParsedFlowCommand:
    """Parse a command path relative to the flows service."""
    segments = normalize_path(path)
    if not segments:
        return ParsedFlowCommand(kind=FlowCommandKind.LIST)
    if len(segments) == 1:
        return ParsedFlowCommand(kind=FlowCommandKind.DESCRIBE, flow_id=segments[0])
    if len(segments) == 2 and segments[1] == "create":
        return ParsedFlowCommand(kind=FlowCommandKind.CREATE, flow_id=segments[0])
    if len(segments) >= 3 and segments[1] == "session":
        flow_id = segments[0]
        session_id = segments[2]
        if len(segments) == 3:
            return ParsedFlowCommand(
                kind=FlowCommandKind.SESSION,
                flow_id=flow_id,
                session_id=session_id,
            )
        if len(segments) == 4:
            verb = segments[3]
            if verb not in _SESSION_VERBS:
                raise ValueError(f"unknown session verb: {verb!r}")
            return ParsedFlowCommand(
                kind=FlowCommandKind.SESSION_VERB,
                flow_id=flow_id,
                session_id=session_id,
                verb=verb,
            )
    joined = "flows " + " ".join(segments)
    raise ValueError(f"unrecognized flow command path: {joined}")


def command_path(
    *,
    flow_id: str | None = None,
    session_id: str | None = None,
    verb: str | None = None,
) -> list[str]:
    """Build a canonical command path for ``next_commands`` hints."""
    parts = ["flows"]
    if flow_id is not None:
        parts.append(flow_id)
    if session_id is not None:
        parts.extend(["session", session_id])
    if verb is not None:
        parts.append(verb)
    return parts


__all__ = [
    "FlowCommandKind",
    "ParsedFlowCommand",
    "command_path",
    "normalize_path",
    "parse_flow_command",
]