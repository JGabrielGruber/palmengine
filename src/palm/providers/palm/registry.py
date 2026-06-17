"""Palm provider registration."""

from palm.core.registry import provider_registry
from palm.providers.palm.provider import PalmProvider

provider_registry.register("palm", PalmProvider)
