"""Flow command-path grammar — parse and build REPL-style command chains.

**0.58.19 vocabulary:** product continue segment is ``instance`` /
``instance_id``. System subject stays out of these paths. Legacy segment
``session`` is still **parsed**; emitters always use ``instance``.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class FlowCommandKind(Enum):
    LIST = "list"
    DESCRIBE = "describe"
    CREATE = "create"
    # Product continue (was SESSION / SESSION_VERB before 0.58.19)
    INSTANCE = "instance"
    INSTANCE_VERB = "instance_verb"

    # Thin aliases for mid-theme call sites.
    SESSION = "instance"
    SESSION_VERB = "instance_verb"


_INSTANCE_VERBS = frozenset(
    {"input", "backtrack", "resume", "cancel"},
)

_CONTINUE_SEGMENTS = frozenset({"instance", "session"})


@dataclass(frozen=True)
class ParsedFlowCommand:
    kind: FlowCommandKind
    flow_id: str | None = None
    instance_id: str | None = None
    verb: str | None = None

    @property
    def session_id(self) -> str | None:
        """Product continue handle — alias of :attr:`instance_id` (SI-002 thin)."""
        return self.instance_id


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
    if len(segments) >= 3 and segments[1] in _CONTINUE_SEGMENTS:
        flow_id = segments[0]
        instance_id = segments[2]
        if len(segments) == 3:
            return ParsedFlowCommand(
                kind=FlowCommandKind.INSTANCE,
                flow_id=flow_id,
                instance_id=instance_id,
            )
        if len(segments) == 4:
            verb = segments[3]
            if verb not in _INSTANCE_VERBS:
                raise ValueError(f"unknown instance verb: {verb!r}")
            return ParsedFlowCommand(
                kind=FlowCommandKind.INSTANCE_VERB,
                flow_id=flow_id,
                instance_id=instance_id,
                verb=verb,
            )
    joined = "flows " + " ".join(segments)
    raise ValueError(f"unrecognized flow command path: {joined}")


def command_path(
    *,
    flow_id: str | None = None,
    instance_id: str | None = None,
    session_id: str | None = None,
    verb: str | None = None,
) -> list[str]:
    """Build a canonical command path for ``next_commands`` hints.

    Prefer ``instance_id``. ``session_id`` is accepted as a legacy kwarg for the
    product continue handle (not the system subject).
    """
    parts = ["flows"]
    if flow_id is not None:
        parts.append(flow_id)
    continue_id = instance_id if instance_id is not None else session_id
    if continue_id is not None:
        parts.extend(["instance", continue_id])
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
