"""0.63.37 — SSR explorer honest voice for closed admission."""

from __future__ import annotations


def operator_error_text(exc: BaseException) -> str:
    """Banner / redirect error text — label gate refusals explicitly.

    Gate is already raised under host packaging / product / port. Explorer
    must not present ``AdmissionRefusedError`` or ``CapabilityRefusedError``
    as a generic form failure.
    """
    from palm.system.structure.errors import (
        AdmissionRefusedError,
        CapabilityRefusedError,
    )

    if isinstance(exc, AdmissionRefusedError):
        return f"admission_refused: {exc}"
    if isinstance(exc, CapabilityRefusedError):
        return f"capability_refused: {exc}"
    return str(exc)


__all__ = ["operator_error_text"]
