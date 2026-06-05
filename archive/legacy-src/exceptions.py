"""
Palm exception hierarchy — general base only (post 0.3.0-dev cleanup).

All engine errors (Behavior Tree Engine, future general components, etc.)
inherit from PalmError.

Wizard-specific, session, validation, and other legacy exceptions have been
moved into `palm.cli.solid.legacy.exceptions` as part of the clean-core migration.
"""

from __future__ import annotations


class PalmError(Exception):
    """Base exception for all Palm engine errors."""

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.code = code or self.__class__.__name__
