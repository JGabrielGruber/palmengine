"""
Embedded runtime — in-process Palm execution for libraries and tests.
"""

from __future__ import annotations

from typing import ClassVar

from palm.runtimes.base import BaseRuntime
from palm.runtimes.wiring import SchedulerPolicy


class EmbeddedRuntime(BaseRuntime):
    """
    In-process runtime coordinating context, events, behavior trees, and jobs.

    Default scheduling is synchronous via
    :class:`~palm.runtimes.schedulers.inline.InlineScheduler`. Pass
    ``scheduler="queued"`` or an explicit scheduler instance to :meth:`start`
    for alternative policies.

    Pass a shared :class:`~palm.core.storage.StorageEngine` to the constructor
    when instances must survive across multiple runtime lifetimes.
    """

    runtime_name: ClassVar[str] = "EmbeddedRuntime"
    default_scheduler_policy: ClassVar[SchedulerPolicy] = "inline"
