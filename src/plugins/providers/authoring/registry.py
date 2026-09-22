"""Authoring provider registration."""

from palm.core.registry import provider_registry
from plugins.providers.authoring.app import authoring_app
from plugins.providers.authoring.provider import AuthoringProvider

provider_registry.register("authoring", AuthoringProvider)
authoring_app.register()
