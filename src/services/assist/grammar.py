"""Assist command-path grammar — parse transport-agnostic assist routes.

**0.58.19 vocabulary:** product continue segment is ``instance`` /
``instance_id``. ``session_id`` is the system subject only (not a path
segment here). Legacy segment ``session`` is still **parsed** for one
slice of soft land; emitters always use ``instance``.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AssistCommandKind(Enum):
    LIST_SCENARIOS = "list_scenarios"
    DESCRIBE_SCENARIO = "describe_scenario"
    START_SCENARIO = "start_scenario"
    SCENARIO_INSPECT = "scenario_inspect"
    # Product continue (was SESSION / SESSION_VERB before 0.58.19)
    INSTANCE = "instance"
    INSTANCE_VERB = "instance_verb"
    DOCTOR = "doctor"
    TOP = "top"
    VITALITY = "vitality"
    CATALOG_FLOWS = "catalog_flows"
    CATALOG_WAITING = "catalog_waiting"
    DISCOVER = "discover"
    MENU = "menu"
    OPEN = "open"

    # Thin aliases so mid-theme call sites and tests can migrate.
    SESSION = "instance"
    SESSION_VERB = "instance_verb"


_INSTANCE_VERBS = frozenset(
    {"input", "backtrack", "resume", "cancel", "handoff"},
)

# Primary product continue segment + legacy parse-only segment.
_CONTINUE_SEGMENTS = frozenset({"instance", "session"})


@dataclass(frozen=True)
class ParsedAssistCommand:
    kind: AssistCommandKind
    scenario_id: str | None = None
    instance_id: str | None = None
    verb: str | None = None

    @property
    def session_id(self) -> str | None:
        """Product continue handle — alias of :attr:`instance_id` (SI-002 thin)."""
        return self.instance_id


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
    if segments == ("top",):
        return ParsedAssistCommand(kind=AssistCommandKind.TOP)
    if segments == ("vitality",):
        return ParsedAssistCommand(kind=AssistCommandKind.VITALITY)
    if segments == ("catalog", "flows"):
        return ParsedAssistCommand(kind=AssistCommandKind.CATALOG_FLOWS)
    if segments == ("catalog", "waiting"):
        return ParsedAssistCommand(kind=AssistCommandKind.CATALOG_WAITING)
    if segments == ("discover",):
        return ParsedAssistCommand(kind=AssistCommandKind.DISCOVER)
    if segments == ("menu",) or (
        len(segments) == 2 and segments[0] == "menu"
    ) or (
        len(segments) == 2 and segments[0] == "catalog" and segments[1] == "menu"
    ):
        return ParsedAssistCommand(kind=AssistCommandKind.MENU)
    if segments == ("open",) or (
        len(segments) == 2 and segments[0] == "catalog" and segments[1] == "open"
    ):
        return ParsedAssistCommand(kind=AssistCommandKind.OPEN)
    if len(segments) >= 2 and segments[0] in _CONTINUE_SEGMENTS:
        instance_id = segments[1]
        if len(segments) == 2:
            return ParsedAssistCommand(
                kind=AssistCommandKind.INSTANCE,
                instance_id=instance_id,
            )
        if len(segments) == 3:
            verb = segments[2]
            if verb not in _INSTANCE_VERBS:
                raise ValueError(f"unknown assist instance verb: {verb!r}")
            return ParsedAssistCommand(
                kind=AssistCommandKind.INSTANCE_VERB,
                instance_id=instance_id,
                verb=verb,
            )
    joined = "assist " + " ".join(segments)
    raise ValueError(f"unrecognized assist command path: {joined}")


def command_path(
    *,
    scenario_id: str | None = None,
    instance_id: str | None = None,
    session_id: str | None = None,
    verb: str | None = None,
) -> list[str]:
    """Build a canonical assist command path for next-command hints.

    Prefer ``instance_id``. ``session_id`` is accepted as a legacy kwarg for the
    product continue handle (not the system subject).
    """
    parts = ["assist"]
    if scenario_id is not None:
        parts.extend(["scenarios", scenario_id])
    continue_id = instance_id if instance_id is not None else session_id
    if continue_id is not None:
        parts.extend(["instance", continue_id])
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
