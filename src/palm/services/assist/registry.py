"""Assist domain contract — scenario contributors and command-path specs."""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

AssistantEnricherFn = Callable[..., dict[str, Any]]


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
    mcp_aliases: tuple[tuple[str, tuple[str, ...]], ...] = ()
    assistant_enricher: AssistantEnricherFn | None = None
    register_routes: Callable[[list[CommandSpec]], None] | None = None
    register_mcp_paths: Callable[[dict[str, tuple[str, ...]]], None] | None = None


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
_mcp_aliases: dict[str, tuple[str, ...]] = {}
_assistant_enrichers: dict[str, AssistantEnricherFn] = {}


def register_assist_contributor(contributor: AssistContributor) -> None:
    """Register an assist scenario contributor (thread-safe, bootstrap time)."""
    with _lock:
        existing = _contributors.get(contributor.scenario_id)
        if existing is contributor:
            return
        _contributors[contributor.scenario_id] = contributor
        for alias, target in contributor.mcp_aliases:
            _mcp_aliases[alias] = target
        if contributor.register_mcp_paths is not None:
            extra: dict[str, tuple[str, ...]] = {}
            contributor.register_mcp_paths(extra)
            _mcp_aliases.update(extra)
        if contributor.assistant_enricher is not None:
            register_assistant_enricher(contributor.scenario_id, contributor.assistant_enricher)


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


def list_mcp_path_aliases() -> list[dict[str, Any]]:
    """Return registered MCP path aliases in stable order."""
    with _lock:
        return [
            {"alias": alias, "path": list(path)}
            for alias, path in sorted(_mcp_aliases.items())
        ]


def resolve_mcp_alias(
    alias: str,
    *,
    params: dict[str, Any] | None = None,
) -> tuple[str, ...] | None:
    """Resolve an alias to a concrete command path, substituting ``params`` tokens."""
    params = params or {}
    with _lock:
        pattern = _mcp_aliases.get(alias)
    if pattern is None:
        return None
    resolved: list[str] = []
    for segment in pattern:
        text = str(segment)
        if text.startswith("{") and text.endswith("}"):
            key = text[1:-1]
            value = params.get(key)
            if value is None:
                raise ValueError(f"alias {alias!r} requires param {key!r}")
            resolved.append(str(value))
        else:
            resolved.append(text)
    return tuple(resolved)


def register_assistant_enricher(scenario_id: str, fn: AssistantEnricherFn) -> None:
    """Register a post-humanize enricher for one assist scenario."""
    with _lock:
        if _assistant_enrichers.get(scenario_id) is fn:
            return
        _assistant_enrichers[scenario_id] = fn


def apply_assistant_enricher(
    scenario_id: str,
    view: dict[str, Any],
    *,
    context: Any,
) -> dict[str, Any]:
    """Apply a scenario enricher when registered."""
    with _lock:
        enricher = _assistant_enrichers.get(scenario_id)
    if enricher is None:
        return view
    enriched = enricher(view, context=context)
    return enriched if isinstance(enriched, dict) else view


def clear_assist_contributors() -> None:
    """Remove assist contributor registrations (primarily for tests)."""
    with _lock:
        _contributors.clear()
        _mcp_aliases.clear()
        _assistant_enrichers.clear()


__all__ = [
    "AssistContributor",
    "CommandSpec",
    "AssistantEnricherFn",
    "apply_assistant_enricher",
    "assist_commands",
    "clear_assist_contributors",
    "list_mcp_path_aliases",
    "list_scenario_rows",
    "register_assist_contributor",
    "register_assistant_enricher",
    "resolve_mcp_alias",
    "scenario_by_id",
]