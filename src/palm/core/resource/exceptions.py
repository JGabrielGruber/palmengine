"""Resource engine exceptions."""

from __future__ import annotations

from palm.core.exceptions import EngineError


class ResourceError(EngineError):
    """Base error for resource coordination failures."""


class ResourceInvokeError(ResourceError):
    """Raised when a provider invocation fails."""


class ResourceResolutionError(ResourceError):
    """Raised when a resource definition cannot be resolved."""