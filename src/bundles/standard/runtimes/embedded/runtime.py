"""
Embedded runtime — in-process Palm execution for libraries and tests.
"""

from __future__ import annotations

from typing import Any, ClassVar

from palm.system.runtime.base import BaseRuntime
from palm.system.runtime.wiring import SchedulerPolicy


class EmbeddedRuntime(BaseRuntime):
    """
    In-process runtime coordinating context, events, behavior trees, and jobs.

    Default scheduling is synchronous via
    :class:`~palm.system.runtime.schedulers.inline.InlineScheduler`. Pass
    ``scheduler="queued"`` or an explicit scheduler instance to :meth:`start`
    for alternative policies.

    Pass a shared :class:`~palm.core.storage.StorageEngine` to the constructor
    when instances must survive across multiple runtime lifetimes.
    """

    runtime_name: ClassVar[str] = "EmbeddedRuntime"
    default_scheduler_policy: ClassVar[SchedulerPolicy] = "inline"

    def start(self, **options: Any) -> None:
        """Name this bundle's storage backend and workload runner when omitted."""
        options.setdefault("storage_backend", "memory")
        options.setdefault("workload_default_runtime", "local")
        super().start(**options)
