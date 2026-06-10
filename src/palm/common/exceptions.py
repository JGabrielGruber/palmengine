"""
Execution-layer exceptions (outside core).
"""

from __future__ import annotations


class ExecutionError(Exception):
    """Base error for definition-driven execution."""


class DefinitionBuildError(ExecutionError):
    """Raised when a flow or process definition cannot be built."""


class DefinitionNotFoundError(ExecutionError):
    """Raised when a definition name or id cannot be resolved."""

    def __init__(self, kind: str, ref: str) -> None:
        super().__init__(f"{kind} definition not found: {ref!r}")
        self.kind = kind
        self.ref = ref


class InstanceNotFoundError(ExecutionError):
    """Raised when a process instance id cannot be loaded."""

    def __init__(self, instance_id: str) -> None:
        super().__init__(f"Process instance not found: {instance_id!r}")
        self.instance_id = instance_id


class InstanceResumeError(ExecutionError):
    """Raised when an instance cannot be resumed (terminal, missing flow, etc.)."""


class InstanceActiveLimitError(ExecutionError):
    """Raised when the active instance limit is exceeded."""


class PlanValidationError(ExecutionError):
    """Raised when an :class:`~palm.common.plans.execution_plan.ExecutionPlan` fails pre-submit checks."""


class PlanNotFoundError(ExecutionError):
    """Raised when a stored plan id cannot be resolved."""

    def __init__(self, plan_id: str) -> None:
        super().__init__(f"Execution plan not found: {plan_id!r}")
        self.plan_id = plan_id
