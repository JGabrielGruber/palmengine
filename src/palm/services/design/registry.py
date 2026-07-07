"""Design service contract — contributor registry and command-path catalog."""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from palm.common.operator.path_alias import resolve_path_alias

DesignValidatorFn = Callable[[dict[str, Any], Any], tuple[bool, list[str]]]


@dataclass(frozen=True)
class CommandSpec:
    """Registered design command path for operator dispatch."""

    command_id: str
    path_pattern: tuple[str, ...]
    summary: str


@dataclass(frozen=True)
class DesignContributor:
    """Pattern- or domain-specific proposal validation hook."""

    contributor_id: str
    validate: DesignValidatorFn | None = None
    summary: str = ""


_registry: tuple[CommandSpec, ...] = (
    CommandSpec("propose_flow", ("design", "propose"), "Create a design proposal from a flow body"),
    CommandSpec("list_proposals", ("design", "proposals"), "List open design proposals"),
    CommandSpec(
        "get_proposal",
        ("design", "proposals", "{proposal_id}"),
        "Load a design proposal envelope",
    ),
    CommandSpec(
        "validate_proposal",
        ("design", "proposals", "{proposal_id}", "validate"),
        "Validate a design proposal",
    ),
    CommandSpec(
        "analyze_impact",
        ("design", "proposals", "{proposal_id}", "impact"),
        "Analyze instance impact for a proposal commit",
    ),
    CommandSpec(
        "commit_proposal",
        ("design", "proposals", "{proposal_id}", "commit"),
        "Publish proposal revision and auto-migrate compatible instances",
    ),
    CommandSpec(
        "discard_proposal",
        ("design", "proposals", "{proposal_id}", "discard"),
        "Discard an open design proposal",
    ),
)

_DESIGN_MCP_ALIASES: dict[str, tuple[str, ...]] = {
    "design/propose": ("design", "propose"),
    "design/list": ("design", "proposals"),
    "design/get": ("design", "proposals", "{proposal_id}"),
    "design/validate": ("design", "proposals", "{proposal_id}", "validate"),
    "design/impact": ("design", "proposals", "{proposal_id}", "impact"),
    "design/commit": ("design", "proposals", "{proposal_id}", "commit"),
    "design/discard": ("design", "proposals", "{proposal_id}", "discard"),
}

_lock = threading.RLock()
_contributors: dict[str, DesignContributor] = {}


def register_design_contributor(contributor: DesignContributor) -> None:
    """Register a design proposal contributor (thread-safe, bootstrap time)."""
    with _lock:
        existing = _contributors.get(contributor.contributor_id)
        if existing is contributor:
            return
        _contributors[contributor.contributor_id] = contributor


def iter_design_contributors() -> tuple[DesignContributor, ...]:
    with _lock:
        return tuple(_contributors.values())


def run_design_validators(body: dict[str, Any], *, context: Any = None) -> tuple[bool, list[str]]:
    """Run registered contributors; aggregate blocker messages."""
    blockers: list[str] = []
    for contributor in iter_design_contributors():
        if contributor.validate is None:
            continue
        ok, messages = contributor.validate(body, context)
        if not ok:
            blockers.extend(messages)
    return (not blockers, blockers)


def clear_design_contributors() -> None:
    """Remove contributor registrations (primarily for tests)."""
    with _lock:
        _contributors.clear()


def design_commands() -> tuple[CommandSpec, ...]:
    return _registry


def list_design_mcp_aliases() -> list[dict[str, Any]]:
    return [
        {"alias": alias, "path": list(path), "domain": "design"}
        for alias, path in sorted(_DESIGN_MCP_ALIASES.items())
    ]


def resolve_design_mcp_alias(
    alias: str,
    *,
    params: dict[str, Any] | None = None,
) -> tuple[str, ...] | None:
    """Resolve a design alias to a concrete command path."""
    return resolve_path_alias(alias, _DESIGN_MCP_ALIASES.get(alias), params=params)


__all__ = [
    "CommandSpec",
    "DesignContributor",
    "DesignValidatorFn",
    "clear_design_contributors",
    "design_commands",
    "iter_design_contributors",
    "list_design_mcp_aliases",
    "register_design_contributor",
    "resolve_design_mcp_alias",
    "run_design_validators",
]