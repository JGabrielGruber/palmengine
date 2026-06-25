"""
Pipeline pattern app manifest — declares Palm layer dependencies and registry hooks.
"""

from __future__ import annotations

from palm.common.patterns.app import PatternApp


class PipelineApp(PatternApp):
    name = "pipeline"
    label = "Sequential pipeline"
    palm_layers = (
        "core.behavior_tree",
        "core.context",
        "core.transform",
        "common.patterns",
        "common.transforms",
        "definitions.flow",
    )
    registry_hooks = ("builder",)


pipeline_app = PipelineApp()

__all__ = ["PipelineApp", "pipeline_app"]