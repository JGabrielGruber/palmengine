"""Service-layer error types."""

from __future__ import annotations

from dataclasses import dataclass

from palm.common.cqrs.schemas import ValidationResult


@dataclass(frozen=True)
class ServiceValidationError(ValueError):
    """Raised when a CQRS payload fails schema validation before dispatch."""

    result: ValidationResult
    cqrs_type: type

    def __str__(self) -> str:
        messages = ", ".join(self.result.errors) or "validation failed"
        return f"{self.cqrs_type.__name__}: {messages}"


class InstanceNotFoundServiceError(LookupError):
    """Raised when a durable instance cannot be resolved."""

    def __init__(self, instance_id: str) -> None:
        self.instance_id = instance_id
        super().__init__(f"Instance not found: {instance_id}")


class DefinitionNotFoundServiceError(LookupError):
    """Raised when a flow, process, or resource definition cannot be resolved."""

    def __init__(self, kind: str, ref: str) -> None:
        self.kind = kind
        self.ref = ref
        super().__init__(f"{kind} not found: {ref}")


class DesignProposalNotFoundServiceError(LookupError):
    """Raised when a design proposal cannot be resolved."""

    def __init__(self, proposal_id: str) -> None:
        self.proposal_id = proposal_id
        super().__init__(f"Design proposal not found: {proposal_id}")


class DesignCommitRejectedServiceError(ValueError):
    """Raised when a design proposal commit is rejected."""

    def __init__(
        self,
        proposal_id: str,
        reason: str,
        *,
        blockers: list[str] | None = None,
    ) -> None:
        self.proposal_id = proposal_id
        self.reason = reason
        self.blockers = list(blockers or [])
        super().__init__(f"Design commit rejected for {proposal_id}: {reason}")


class InstanceMigrationServiceError(ValueError):
    """Raised when an instance migration request cannot be applied."""

    def __init__(
        self,
        instance_id: str,
        reason: str,
        *,
        blockers: list[str] | None = None,
        result: dict[str, object] | None = None,
    ) -> None:
        self.instance_id = instance_id
        self.reason = reason
        self.blockers = list(blockers or [])
        self.result = result
        super().__init__(f"Instance migration failed for {instance_id}: {reason}")


__all__ = [
    "DefinitionNotFoundServiceError",
    "DesignCommitRejectedServiceError",
    "DesignProposalNotFoundServiceError",
    "InstanceMigrationServiceError",
    "InstanceNotFoundServiceError",
    "ServiceValidationError",
]
