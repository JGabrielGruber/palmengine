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


__all__ = [
    "DefinitionNotFoundServiceError",
    "InstanceNotFoundServiceError",
    "ServiceValidationError",
]