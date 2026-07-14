"""Bootstrap design contributors after service domains are wired."""

from __future__ import annotations

import threading

_lock = threading.RLock()
_wired = False


def wire_builtin_design_contributors() -> None:
    """Drain pattern-registered design hooks into the design service registry (idempotent)."""
    global _wired
    with _lock:
        if _wired:
            return
        from palm.patterns._registry import iter_design_contributor_hooks

        for hook in iter_design_contributor_hooks():
            hook.register()
        from palm.providers._registry import iter_provider_design_contributor_hooks

        for hook in iter_provider_design_contributor_hooks():
            hook()
        # 0.41.2 — dashboard tile validation
        from palm.services.analytics.dashboard_design import (
            validate_dashboard_design_proposal,
        )
        from palm.services.design.registry import (
            DesignContributor,
            register_design_contributor,
        )

        register_design_contributor(
            DesignContributor(
                contributor_id="dashboard",
                validate=validate_dashboard_design_proposal,
                summary="Dashboard tile structure and profile validation (0.41)",
            ),
        )
        _wired = True


def reset_design_contributor_wiring() -> None:
    """Reset wiring flag (tests only)."""
    global _wired
    with _lock:
        _wired = False


__all__ = ["reset_design_contributor_wiring", "wire_builtin_design_contributors"]