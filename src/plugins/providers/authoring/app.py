"""Authoring resource provider — job leaf walks the authoring adapter."""

from __future__ import annotations

from palm.common.providers.app import ProviderApp


class AuthoringApp(ProviderApp):
    name = "authoring"
    label = "Catalog commit through palm.kits.authoring"
    palm_layers = ("kits.authoring", "definitions")
    actions = ("commit",)
    registry_hooks = ("provider_registry",)


authoring_app = AuthoringApp()

__all__ = ["AuthoringApp", "authoring_app"]
