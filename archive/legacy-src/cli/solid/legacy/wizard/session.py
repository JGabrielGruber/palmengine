"""
Lightweight session-related helpers for the wizard engine.

Most session logic lives in models.session.WizardSession.
This module exists for future extension (e.g. snapshotting, replay).
"""

from __future__ import annotations

from palm.cli.solid.legacy.models.session import WizardSession as WizardSessionState

__all__ = ["WizardSessionState"]
