"""WorkloadRuntime registry — name → runtime class (bootstrap registration).

Registration of concrete runners happens outside core (``palm.runners``).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.core.registry import Registry

if TYPE_CHECKING:
    from palm.core.workload.protocol import WorkloadRuntime

workload_runtime_registry: Registry[type[WorkloadRuntime]] = Registry("workload runtime")
