"""Assist command-path grammar — parse transport-agnostic assist routes."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AssistCommandKind(Enum):
    LIST_SCENARIOS = "list_scenarios"
    DESCRIBE_SCENARIO = "describe_scenario"
    START_SCENARIO = "start_scenario"
    SCENARIO_INSPECT = "scenario_inspect"
    SESSION = "session"
    SESSION_VERB = "session_verb"
    DOCTOR = "doctor"
    CATALOG_FLOWS = "catalog_flows"
    CATALOG_WAITING = "catalog_waiting"
    DISCOVER = "discover"


_SESSION_VERBS = frozenset(
    {"input", "backtrack", "resume", "cancel", "handoff"},
)


@dataclass(frozen=True)
class ParsedAssistCommand:
    kind: AssistCommandKind
    scenario_id: str | None = None
    session_id: str | None = None
    verb: str | None = None


def normalize_path(path: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    segments = tuple(str(segment) for segment in path)
    if segments and segments[0] == "assist":
        return segments[1:]
    return segments


def parse_assist_command(path: list[str] | tuple[str, ...]) -> ParsedAssistCommand:
    """Parse a command path relative to the assist service."""
    segments = normalize_path(path)
    if not segments:
        raise ValueError("assist command path must not be empty")
    if segments == ("scenarios",):
        return ParsedAssistCommand(kind=AssistCommandKind.LIST_SCENARIOS)
    if len(segments) == 2 and segments[0] == "scenarios" and segments[1] != "start":
        return ParsedAssistCommand(
            kind=AssistCommandKind.DESCRIBE_SCENARIO,
            scenario_id=segments[1],
        )
    if len(segments) == 3 and segments[0] == "scenarios" and segments[2] == "start":
        return ParsedAssistCommand(
            kind=AssistCommandKind.START_SCENARIO,
            scenario_id=segments[1],
        )
    if len(segments) == 3 and segments[0] == "scenarios" and segments[2] == "inspect":
        return ParsedAssistCommand(
            kind=AssistCommandKind.SCENARIO_INSPECT,
            scenario_id=segments[1],
        )
    if segments == ("doctor",):
        return ParsedAssistCommand(kind=AssistCommandKind.DOCTOR)
    if segments == ("catalog", "flows"):
        return ParsedAssistCommand(kind=AssistCommandKind.CATALOG_FLOWS)
    if segments == ("catalog", "waiting"):
        return ParsedAssistCommand(kind=AssistCommandKind.CATALOG_WAITING)
    if segments == ("discover",):
        return ParsedAssistCommand(kind=AssistCommandKind.DISCOVER)
    if len(segments) >= 2 and segments[0] == "session":
        session_id = segments[1]
        if len(segments) == 2:
            return ParsedAssistCommand(
                kind=AssistCommandKind.SESSION,
                session_id=session_id,
            )
        if len(segments) == 3:
            verb = segments[2]
            if verb not in _SESSION_VERBS:
                raise ValueError(f"unknown assist session verb: {verb!r}")
            return ParsedAssistCommand(
                kind=AssistCommandKind.SESSION_VERB,
                session_id=session_id,
                verb=verb,
            )
    joined = "assist " + " ".join(segments)
    raise ValueError(f"unrecognized assist command path: {joined}")


def command_path(
    *,
    scenario_id: str | None = None,
    session_id: str | None = None,
    verb: str | None = None,
) -> list[str]:
    """Build a canonical assist command path for next-command hints."""
    parts = ["assist"]
    if scenario_id is not None:
        parts.extend(["scenarios", scenario_id])
    if session_id is not None:
        parts.extend(["session", session_id])
    if verb is not None:
        parts.append(verb)
    return parts


__all__ = [
    "AssistCommandKind",
    "ParsedAssistCommand",
    "command_path",
    "normalize_path",
    "parse_assist_command",
]