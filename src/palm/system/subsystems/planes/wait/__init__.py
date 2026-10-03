"""Continue plane — wait interest match / present (0.55 Reactive Interests).

Pure interest types live in :mod:`palm.core.wait`. Coordination and
:class:`~palm.system.subsystems.planes.wait.plane.WaitPlaneService` live here.

**Public door (0.55.15)** — production open/match/present only:

* :class:`WaitPlaneService`
* :func:`get_wait_plane` and :func:`open_interest_on_job` (etc.) when
  callers pass the continue plane and the orchestration they already hold
* :mod:`~palm.system.subsystems.planes.wait.present` helpers for operator surfaces

Internals (import the submodule): ``matcher``, ``index``, ``signals``,
``policy``, ``deliver``, ``rehydrate``, ``workload_stub``.
"""

from palm.system.subsystems.planes.wait.access import (
    close_interest_for_state,
    close_interest_on_job,
    find_job_for_state,
    get_wait_plane,
    open_interest_for_state,
    open_interest_on_job,
)
from palm.system.subsystems.planes.wait.plane import WaitPlaneService
from palm.system.subsystems.planes.wait.present import (
    summarize_waiting_on,
    waiting_on_from_job,
    waiting_on_from_state,
    waiting_on_row,
)

__all__ = [
    "WaitPlaneService",
    "close_interest_for_state",
    "close_interest_on_job",
    "find_job_for_state",
    "get_wait_plane",
    "open_interest_for_state",
    "open_interest_on_job",
    "summarize_waiting_on",
    "waiting_on_from_job",
    "waiting_on_from_state",
    "waiting_on_row",
]
