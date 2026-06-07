"""Rest provider registration."""

from palm.core.registry import provider_registry
from palm.providers.rest.provider import RestProvider

provider_registry.register("rest", RestProvider)
