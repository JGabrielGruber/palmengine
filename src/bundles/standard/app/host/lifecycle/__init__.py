"""
Host lifecycle (T2 / 0.48.4, seam 5) — runtime spawning + startup recovery.

Collaborators the host drives during ``start``: ``RuntimeSpawner`` creates the
runtimes a profile calls for; ``RecoveryCoordinator`` handles worker readiness,
compensation, webhook seat, and projection rebuild.
"""

from __future__ import annotations

from bundles.standard.app.host.lifecycle.recovery import RecoveryCoordinator
from bundles.standard.app.host.lifecycle.spawn import RuntimeSpawner

__all__ = ["RecoveryCoordinator", "RuntimeSpawner"]
