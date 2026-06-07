"""
Legacy instance persistence wiring — prefer :class:`~palm.executions.hooks.InstancePersistenceHook`.
"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

from palm.core.orchestration.job import JobStatus
from palm.executions.hooks import InstancePersistenceHook

if TYPE_CHECKING:
    from palm.executions.instance_repository import InstanceRepository
    from palm.runtimes.embedded import EmbeddedRuntime


def wire_instance_persistence(
    runtime: EmbeddedRuntime,
    instances: InstanceRepository,
) -> None:
    """
    Deprecated: instance persistence is registered via ``InstancePersistenceHook`` at runtime start.
    """
    warnings.warn(
        "wire_instance_persistence is deprecated; EmbeddedRuntime registers "
        "InstancePersistenceHook automatically (0.6+)",
        DeprecationWarning,
        stacklevel=2,
    )
    hook = InstancePersistenceHook(instances)
    runtime.orchestration._hooks.append(hook)


def is_resumable_status(status: str) -> bool:
    return status in (
        JobStatus.WAITING_FOR_INPUT.value,
        JobStatus.RUNNING.value,
        JobStatus.PENDING.value,
    )