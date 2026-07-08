"""File document provider registration."""

from palm.core.registry import provider_registry
from palm.providers.file.app import file_app
from palm.providers.file.provider import FileProvider

provider_registry.register("file", FileProvider)
file_app.register()