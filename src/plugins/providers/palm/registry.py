"""Palm provider registration."""

from palm.core.registry import provider_registry
from plugins.providers.palm.app import palm_app
from plugins.providers.palm.provider import PalmProvider

provider_registry.register("palm", PalmProvider)
palm_app.register()
