"""Design service contract — contributor registry for proposal validation."""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

DesignValidatorFn = Callable[[dict[str, Any], Any], tuple[bool, list[str]]]


@dataclass(frozen=True)
class DesignContributor:
    """Pattern- or domain-specific proposal validation hook."""

    contributor_id: str
    validate: DesignValidatorFn | None = None
    summary: str = ""


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


__all__ = [
    "DesignContributor",
    "DesignValidatorFn",
    "clear_design_contributors",
    "iter_design_contributors",
    "register_design_contributor",
    "run_design_validators",
]