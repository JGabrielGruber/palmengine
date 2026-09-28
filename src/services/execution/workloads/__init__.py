"""Workload product API under the execution domain."""

from services.execution.workloads.bindings.cqrs import contributor as _cqrs  # noqa: F401
from services.execution.workloads.service import WorkloadExecutionService

__all__ = ["WorkloadExecutionService"]
