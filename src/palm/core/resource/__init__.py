"""
Resource engine — abstract provider coordination.

Pure core module: no imports from outside ``palm.core``.
"""

from palm.core.resource.base_provider import BaseProvider
from palm.core.resource.engine import ResourceEngine
from palm.core.resource.exceptions import (
    ResourceError,
    ResourceInvokeError,
    ResourceResolutionError,
)
from palm.core.resource.invocation import (
    ResolvedResourceSpec,
    bind_resource_id,
    bind_resource_params,
    bind_resource_value,
)
from palm.core.resource.result import (
    ProviderActionDescriptor,
    ProviderDescriptor,
    ProviderHealth,
    ProviderResult,
)

__all__ = [
    "BaseProvider",
    "ProviderActionDescriptor",
    "ProviderDescriptor",
    "ProviderHealth",
    "ProviderResult",
    "ResolvedResourceSpec",
    "ResourceEngine",
    "ResourceError",
    "ResourceInvokeError",
    "ResourceResolutionError",
    "bind_resource_id",
    "bind_resource_params",
    "bind_resource_value",
]
