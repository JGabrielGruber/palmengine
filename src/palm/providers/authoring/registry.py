"""Authoring provider registration."""

from palm.core.registry import provider_registry
from palm.providers.authoring.app import authoring_app
from palm.providers.authoring.provider import AuthoringProvider

provider_registry.register("authoring", AuthoringProvider)
authoring_app.register()
