"""Assist domain contract — scenario contributors and command-path specs."""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CommandSpec:
    """Declarative assist command path owned by the assist service domain."""

    command_id: str
    path_pattern: tuple[str, ...]
    summary: str = ""


@dataclass(frozen=True)
class AssistContributor:
    """Registered assist scenario — maps scenario id to catalog flow id."""

    contributor_id: str
    scenario_id: str
    flow_id: str
    summary: str = ""
    register_routes: Callable[[list[CommandSpec]], None] | None = None
    register_mcp_paths: Callable[[dict[str, str]], None] | None = None


_registry: list[CommandSpec] = [
    CommandSpec("list_scenarios", ("assist", "scenarios"), "List registered assist scenarios"),
    CommandSpec(
        "describe_scenario",
        ("assist", "scenarios", "{scenario_id}"),
        "Describe one assist scenario",
    ),
    CommandSpec(
        "start_scenario",
        ("assist", "scenarios", "{scenario_id}", "start"),
        "Start an assist scenario session",
    ),
    CommandSpec(
        "session_context",
        ("assist", "session", "{session_id}"),
        "Inspect an assist session",
    ),
    CommandSpec(
        "session_input",
        ("assist", "session", "{session_id}", "input"),
        "Provide interactive input to an assist session",
    ),
    CommandSpec(
        "session_backtrack",
        ("assist", "session", "{session_id}", "backtrack"),
        "Backtrack an assist session to a prior step",
    ),
    CommandSpec(
        "session_resume",
        ("assist", "session", "{session_id}", "resume"),
        "Resume a waiting assist session",
    ),
    CommandSpec(
        "session_cancel",
        ("assist", "session", "{session_id}", "cancel"),
        "Cancel an assist session job",
    ),
    CommandSpec(
        "session_handoff",
        ("assist", "session", "{session_id}", "handoff"),
        "Emit handoff payload for business flow entry",
    ),
    CommandSpec("doctor", ("assist", "doctor"), "Engine health report shortcut"),
    CommandSpec(
        "catalog_flows",
        ("assist", "catalog", "flows"),
        "List runnable flows from the definition catalog",
    ),
]

_lock = threading.RLock()
_contributors: dict[str, AssistContributor] = {}


def register_assist_contributor(contributor: AssistContributor) -> None:
    """Register an assist scenario contributor (thread-safe, bootstrap time)."""
    with _lock:
        existing = _contributors.get(contributor.scenario_id)
        if existing is contributor:
            return
        _contributors[contributor.scenario_id] = contributor


def assist_commands() -> tuple[CommandSpec, ...]:
    return tuple(_registry)


def list_scenario_rows() -> list[dict[str, Any]]:
    """Return registered scenario rows in stable scenario-id order."""
    with _lock:
        contributors = [_contributors[key] for key in sorted(_contributors)]
    return [
        {
            "scenario_id": row.scenario_id,
            "flow_id": row.flow_id,
            "summary": row.summary,
            "contributor_id": row.contributor_id,
        }
        for row in contributors
    ]


def scenario_by_id(scenario_id: str) -> AssistContributor | None:
    with _lock:
        return _contributors.get(scenario_id)


def clear_assist_contributors() -> None:
    """Remove assist contributor registrations (primarily for tests)."""
    with _lock:
        _contributors.clear()


__all__ = [
    "AssistContributor",
    "CommandSpec",
    "assist_commands",
    "clear_assist_contributors",
    "list_scenario_rows",
    "register_assist_contributor",
    "scenario_by_id",
]