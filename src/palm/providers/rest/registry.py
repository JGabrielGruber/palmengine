"""Rest provider registration."""

from palm.core.registry import provider_registry
from palm.providers.rest.app import rest_app
from palm.providers.rest.provider import RestProvider

provider_registry.register("rest", RestProvider)
rest_app.register()
