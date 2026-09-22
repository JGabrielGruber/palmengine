"""File document provider registration."""

from palm.core.registry import provider_registry
from plugins.providers.file.app import file_app
from plugins.providers.file.provider import FileProvider

provider_registry.register("file", FileProvider)
file_app.register()