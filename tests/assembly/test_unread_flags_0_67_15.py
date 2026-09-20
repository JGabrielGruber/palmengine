"""Unread packaging flags are gone (0.67.15). Membership is DNA."""

from __future__ import annotations

from palm.app.settings import PalmSettings
from palm.common.compensation.coordinator import CompensationCoordinator
from palm.common.cqrs.projection import ProjectionManager


def test_packaging_has_no_unread_organ_flags() -> None:
    """DNA lists the name. Settings do not keep a dead switch."""
    assert "enable_compensation" not in PalmSettings.__dataclass_fields__
    assert "enable_webhook_dispatcher" not in PalmSettings.__dataclass_fields__


def test_coordinator_has_no_attach_runtimes() -> None:
    """Dual-bus leftover. Attach is one organ on the runtime bus (0.67.12)."""
    assert not hasattr(CompensationCoordinator, "attach_runtimes")


def test_projections_have_no_attach_runtimes() -> None:
    """Dual-bus leftover. Attach is one organ on the runtime bus (0.67.10)."""
    assert not hasattr(ProjectionManager, "attach_runtimes")
