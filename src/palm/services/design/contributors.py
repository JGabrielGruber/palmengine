"""Bootstrap design contributors after service domains are wired."""

from __future__ import annotations

import threading

_lock = threading.RLock()
_wired = False


def wire_builtin_design_contributors() -> None:
    """Register pattern-owned design validators (idempotent)."""
    global _wired
    with _lock:
        if _wired:
            return
        from palm.patterns.wizard.bindings.design import register_wizard_design_contributor

        register_wizard_design_contributor()
        _wired = True


def reset_design_contributor_wiring() -> None:
    """Reset wiring flag (tests only)."""
    global _wired
    with _lock:
        _wired = False


__all__ = ["reset_design_contributor_wiring", "wire_builtin_design_contributors"]