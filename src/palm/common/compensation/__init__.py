"""
Compensation — optional saga-style undo hooks for failed commits and backtracking.

**Add a compensation handler**

1. Implement a callable ``(CompensationContext) -> CompensationResult``.
2. Register on :func:`default_compensation_registry` during definition bootstrap::

       from palm.common.compensation import (
           CompensationContext,
           CompensationResult,
           default_compensation_registry,
       )

       def undo_save(ctx: CompensationContext) -> CompensationResult:
           # reverse partial writes using ctx.payload / ctx.metadata
           return CompensationResult.success({"undone": True})

       default_compensation_registry().register_for_commit_hook("save_profile", undo_save)

   For mutating resource steps, register by ``resource_ref`` (or ``compensation_key`` in
   definition metadata)::

       default_compensation_registry().register_for_resource("submit-ingest-etl", undo_etl)

3. Optionally register per-event handlers for backtrack or custom saga steps::

       registry.register_for_event("wizard.backtrack.executed", my_handler)

4. :class:`~palm.app.host.ApplicationHost` wires
   :class:`~palm.common.compensation.coordinator.CompensationCoordinator` on start
   when ``enable_compensation=True`` (default).
"""

from palm.common.compensation.context import CompensationContext, CompensationResult
from palm.common.compensation.coordinator import CompensationCoordinator
from palm.common.compensation.events import CompensationEventType, CompensationTrigger
from palm.common.compensation.registry import (
    CompensationHandler,
    CompensationRegistry,
    default_compensation_registry,
)

__all__ = [
    "CompensationContext",
    "CompensationCoordinator",
    "CompensationEventType",
    "CompensationHandler",
    "CompensationRegistry",
    "CompensationResult",
    "CompensationTrigger",
    "default_compensation_registry",
]
