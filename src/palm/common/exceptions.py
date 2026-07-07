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


class DesignProposalNotFoundError(ExecutionError):
    """Raised when a design proposal id cannot be loaded."""

    def __init__(self, proposal_id: str) -> None:
        super().__init__(f"Design proposal not found: {proposal_id!r}")
        self.proposal_id = proposal_id


class DesignCommitRejectedError(ExecutionError):
    """Raised when a design proposal cannot be committed."""

    def __init__(
        self,
        proposal_id: str,
        reason: str,
        *,
        blockers: list[str] | None = None,
    ) -> None:
        super().__init__(f"Design commit rejected for {proposal_id!r}: {reason}")
        self.proposal_id = proposal_id
        self.reason = reason
        self.blockers = list(blockers or [])


class InstanceMigrationError(ExecutionError):
    """Raised when an instance cannot migrate to a target flow revision."""

    def __init__(
        self,
        instance_id: str,
        reason: str,
        *,
        blockers: list[str] | None = None,
    ) -> None:
        super().__init__(f"Instance migration failed for {instance_id!r}: {reason}")
        self.instance_id = instance_id
        self.reason = reason
        self.blockers = list(blockers or [])


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


class MutationRejectedError(ExecutionError):
    """Raised when a wizard mutation lacks a valid ``input_token`` in strict mode."""

    def __init__(
        self,
        *,
        reason: str,
        session_id: str,
        step_slug: str,
        detail: str,
    ) -> None:
        super().__init__(f"mutation_rejected: {detail}")
        self.reason = reason
        self.session_id = session_id
        self.step_slug = step_slug
        self.detail = detail
