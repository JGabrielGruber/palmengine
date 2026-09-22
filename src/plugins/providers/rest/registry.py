"""Rest provider registration."""

from palm.core.registry import provider_registry
from plugins.providers.rest.app import rest_app
from plugins.providers.rest.provider import RestProvider

provider_registry.register("rest", RestProvider)
rest_app.register()
