"""
Application-level assist contributor registry.

Downstream Palm applications register optional assist scenarios alongside
service-owned built-in contributors.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass

from palm.services.assist.registry import AssistContributor, register_assist_contributor


@dataclass(frozen=True)
class AppAssistContributor:
    """Application-owned assist scenario registered at bootstrap."""

    app_name: str
    contributor: AssistContributor


_lock = threading.RLock()
_contributors: dict[str, AppAssistContributor] = {}


def register_app_assist_contributor(contributor: AppAssistContributor) -> None:
    """Register application-owned assist scenarios on the assist service."""
    with _lock:
        existing = _contributors.get(contributor.app_name)
        if existing is contributor:
            return
        _contributors[contributor.app_name] = contributor
        register_assist_contributor(contributor.contributor)


def get_app_assist_contributor(name: str) -> AppAssistContributor | None:
    with _lock:
        return _contributors.get(name)


def iter_app_assist_contributors() -> list[AppAssistContributor]:
    with _lock:
        return [_contributors[name] for name in sorted(_contributors)]


def clear_app_assist_contributors() -> None:
    with _lock:
        _contributors.clear()


__all__ = [
    "AppAssistContributor",
    "clear_app_assist_contributors",
    "get_app_assist_contributor",
    "iter_app_assist_contributors",
    "register_app_assist_contributor",
]