"""Process command-path grammar — parse REPL-style command chains."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ProcessCommandKind(Enum):
    PREPARE = "prepare"
    SUBMIT = "submit"
    RUN = "run"


@dataclass(frozen=True)
class ParsedProcessCommand:
    kind: ProcessCommandKind
    process_id: str | None = None


def normalize_path(path: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    segments = tuple(str(segment) for segment in path)
    if segments and segments[0] == "processes":
        return segments[1:]
    return segments


def parse_process_command(path: list[str] | tuple[str, ...]) -> ParsedProcessCommand:
    """Parse a command path relative to the processes execution service."""
    segments = normalize_path(path)
    if not segments:
        raise ValueError("process command path requires at least one segment")
    if len(segments) == 1 and segments[0] == "submit":
        return ParsedProcessCommand(kind=ProcessCommandKind.SUBMIT)
    if len(segments) == 2 and segments[1] == "prepare":
        return ParsedProcessCommand(
            kind=ProcessCommandKind.PREPARE,
            process_id=segments[0],
        )
    if len(segments) == 2 and segments[1] == "run":
        return ParsedProcessCommand(
            kind=ProcessCommandKind.RUN,
            process_id=segments[0],
        )
    joined = "processes " + " ".join(segments)
    raise ValueError(f"unrecognized process command path: {joined}")


__all__ = [
    "ParsedProcessCommand",
    "ProcessCommandKind",
    "normalize_path",
    "parse_process_command",
]