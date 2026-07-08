"""File document provider app manifest."""

from __future__ import annotations

from palm.common.providers.app import ProviderApp


class FileApp(ProviderApp):
    name = "file"
    label = "Local filesystem document resources"
    palm_layers = ("core.resource",)
    actions = ("read", "write", "delete", "exists", "list")
    registry_hooks = ("provider_registry", "design_contributor")

    def ready(self) -> None:
        from palm.providers._registry import register_provider_design_contributor_hook

        def _register_file_design_contributor() -> None:
            from palm.providers.file.bindings.design import register_file_design_contributor

            register_file_design_contributor()

        register_provider_design_contributor_hook(_register_file_design_contributor)


file_app = FileApp()

__all__ = ["FileApp", "file_app"]