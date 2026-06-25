"""
Palm provider app manifest — declares Palm layer dependencies and registry hooks.

Read this file first to understand which Palm subsystems the palm provider dogfoods.
"""

from __future__ import annotations

from palm.common.providers.app import ProviderApp
from palm.providers._registry import register_runtime_binding
from palm.providers.palm.bindings.runtimes.wiring import bind_palm_runtime, clear_palm_runtime


class PalmProviderApp(ProviderApp):
    name = "palm"
    label = "Compositional Palm orchestration"
    palm_layers = (
        "core.resource",
        "core.orchestration",
        "core.utils.recursion",
        "common.runtimes",
        "definitions.resource",
        "instances",
        "runtimes.server",
    )
    actions = ("submit_flow", "submit_process", "invoke_resource", "fetch")
    registry_hooks = ("provider_registry", "runtime_binding")

    def ready(self) -> None:
        register_runtime_binding(bind_palm_runtime, unbind=clear_palm_runtime)


palm_app = PalmProviderApp()

__all__ = ["PalmProviderApp", "palm_app"]