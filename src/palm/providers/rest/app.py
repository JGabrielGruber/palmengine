"""REST provider app manifest."""

from __future__ import annotations

from palm.common.providers.app import ProviderApp


class RestApp(ProviderApp):
    name = "rest"
    label = "HTTP REST resource access"
    palm_layers = ("core.resource",)
    actions = ("fetch",)
    registry_hooks = ("provider_registry",)


rest_app = RestApp()

__all__ = ["RestApp", "rest_app"]