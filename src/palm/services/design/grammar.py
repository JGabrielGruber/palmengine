"""Design command-path grammar — resolve paths via :func:`design_commands` registry."""

from __future__ import annotations

from dataclasses import dataclass

from palm.common.operator.path_match import match_command_path
from palm.services.design.registry import CommandSpec, design_commands


@dataclass(frozen=True)
class ResolvedDesignCommand:
    """Matched design command with path captures."""

    spec: CommandSpec
    capture: dict[str, str]


def resolve_design_command(path: list[str] | tuple[str, ...]) -> ResolvedDesignCommand:
    """Match ``path`` against registered :func:`design_commands` patterns."""
    segments = tuple(str(segment) for segment in path)
    for spec in design_commands():
        capture = match_command_path(segments, spec.path_pattern)
        if capture is not None:
            return ResolvedDesignCommand(spec=spec, capture=capture)
    joined = "/".join(segments)
    raise ValueError(f"unrecognized design dispatch path: {joined}")


__all__ = ["ResolvedDesignCommand", "resolve_design_command"]