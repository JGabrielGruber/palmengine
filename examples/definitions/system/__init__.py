"""
System ops datasets via the Palm provider (local or remote_url).

Registration order: resources → dashboard.
"""

from __future__ import annotations

from . import dashboard, resources

__all__ = ["dashboard", "resources", "register_definitions"]


def register_definitions(repository: object) -> None:
    resources.register_definitions(repository)
    dashboard.register_definitions(repository)
