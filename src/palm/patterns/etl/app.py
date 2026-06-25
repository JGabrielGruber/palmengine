"""
ETL pattern app manifest — declares Palm layer dependencies and registry hooks.

Execution logic is still a placeholder; ``flow/`` is reserved for extract/load stages.
"""

from __future__ import annotations

from palm.common.patterns.app import PatternApp


class EtlApp(PatternApp):
    name = "etl"
    label = "Extract-transform-load pipeline"
    palm_layers = (
        "core.behavior_tree",
        "core.context",
        "core.transform",
        "common.patterns",
        "common.transforms",
        "definitions.flow",
    )
    registry_hooks = ("builder",)


etl_app = EtlApp()

__all__ = ["EtlApp", "etl_app"]