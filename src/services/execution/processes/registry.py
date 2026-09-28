"""Process execution contract — command-path specs (transport-agnostic)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CommandSpec:
    """Declarative process command path owned by the processes execution domain."""

    command_id: str
    path_pattern: tuple[str, ...]
    summary: str = ""


_registry: list[CommandSpec] = [
    CommandSpec(
        "prepare",
        ("processes", "{process_id}", "prepare"),
        "Stage execution plans for a process",
    ),
    CommandSpec("submit", ("processes", "submit"), "Submit staged plan ids"),
    CommandSpec(
        "run",
        ("processes", "{process_id}", "run"),
        "Prepare and submit a process in one call",
    ),
]


def process_commands() -> tuple[CommandSpec, ...]:
    return tuple(_registry)


__all__ = ["CommandSpec", "process_commands"]