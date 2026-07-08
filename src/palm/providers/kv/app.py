"""KV provider app manifest."""

from __future__ import annotations

from palm.common.providers.app import ProviderApp


class KvApp(ProviderApp):
    name = "kv"
    label = "Local key-value resource storage"
    palm_layers = ("core.resource", "core.storage")
    actions = ("get", "put", "delete", "list")
    registry_hooks = ("provider_registry",)


kv_app = KvApp()

__all__ = ["KvApp", "kv_app"]