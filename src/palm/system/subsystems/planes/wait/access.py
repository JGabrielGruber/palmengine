"""Open and close wait interests for a caller that has a job or a state.

Prefer :meth:`~palm.system.subsystems.planes.wait.plane.WaitPlaneService.open_on_job` when the
caller already holds the continue plane. These helpers take that plane and the
orchestration the caller holds. A missing plane uses pure :mod:`palm.core.wait`
open and close.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.core.wait import (
    WaitInterest,
    close_wait_interest,
    close_wait_on_job,
    open_wait_interest,
    open_wait_on_job,
)

if TYPE_CHECKING:
    from palm.system.subsystems.planes.wait.plane import WaitPlaneService


def get_wait_plane(plane: WaitPlaneService | None = None) -> WaitPlaneService | None:
    """Return the continue plane the caller passes."""
    return plane


def find_job_for_state(state: Any, *, orchestration: Any | None = None) -> Any | None:
    """Locate a live job whose ``.state`` is ``state`` (identity)."""
    if orchestration is None:
        return None
    for job in list(orchestration.jobs.values()):
        if getattr(job, "state", None) is state:
            return job
    return None


def open_interest_on_job(
    job: Any,
    interest: WaitInterest,
    *,
    plane: WaitPlaneService | None = None,
    **kwargs: Any,
) -> WaitInterest:
    """Open via the continue plane the caller passes; else pure state open."""
    bound = get_wait_plane(plane)
    if bound is not None:
        return bound.open_on_job(job, interest, **kwargs)
    return open_wait_on_job(job, interest, **kwargs)


def close_interest_on_job(
    job: Any,
    *,
    kind: str,
    target_id: str,
    plane: WaitPlaneService | None = None,
) -> WaitInterest | None:
    """Close via the continue plane the caller passes; else pure state close."""
    bound = get_wait_plane(plane)
    if bound is not None:
        return bound.close_on_job(job, kind=kind, target_id=target_id)
    return close_wait_on_job(job, kind=kind, target_id=target_id)


def open_interest_for_state(
    state: Any,
    interest: WaitInterest,
    *,
    plane: WaitPlaneService | None = None,
    orchestration: Any | None = None,
    **kwargs: Any,
) -> WaitInterest:
    """Open interest on the caller plane when the owner job is live."""
    job = find_job_for_state(state, orchestration=orchestration)
    if job is not None:
        return open_interest_on_job(job, interest, plane=plane, **kwargs)
    return open_wait_interest(state, interest, **kwargs)


def close_interest_for_state(
    state: Any,
    *,
    kind: str,
    target_id: str,
    plane: WaitPlaneService | None = None,
    orchestration: Any | None = None,
) -> WaitInterest | None:
    """Close interest on the caller plane when the owner job is live."""
    job = find_job_for_state(state, orchestration=orchestration)
    if job is not None:
        return close_interest_on_job(
            job,
            kind=kind,
            target_id=target_id,
            plane=plane,
        )
    return close_wait_interest(state, kind=kind, target_id=target_id)


__all__ = [
    "close_interest_for_state",
    "close_interest_on_job",
    "find_job_for_state",
    "get_wait_plane",
    "open_interest_for_state",
    "open_interest_on_job",
]
