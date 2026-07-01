"""Shared service primitives — domain services live in ``palm.services``."""

from palm.common.services.base import BaseService
from palm.common.services.errors import (
    DefinitionNotFoundServiceError,
    InstanceNotFoundServiceError,
    ServiceValidationError,
)

__all__ = [
    "BaseService",
    "DefinitionNotFoundServiceError",
    "InstanceNotFoundServiceError",
    "ServiceValidationError",
]