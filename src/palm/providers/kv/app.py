"""KV provider app manifest."""

from __future__ import annotations

from palm.common.providers.app import ProviderApp


class KvApp(ProviderApp):
    name = "kv"
    label = "Local key-value resource storage"
    palm_layers = ("core.resource", "core.storage")
    actions = ("get", "put", "delete", "list")
    registry_hooks = ("provider_registry", "design_contributor")

    def ready(self) -> None:
        from palm.providers._registry import register_provider_design_contributor_hook

        def _register_kv_design_contributor() -> None:
            from palm.providers.kv.bindings.design import register_kv_design_contributor

            register_kv_design_contributor()

        def _register_file_design_contributor() -> None:
            from palm.providers.file.bindings.design import register_file_design_contributor

            register_file_design_contributor()

        register_provider_design_contributor_hook(_register_kv_design_contributor)
        register_provider_design_contributor_hook(_register_file_design_contributor)


kv_app = KvApp()

__all__ = ["KvApp", "kv_app"]