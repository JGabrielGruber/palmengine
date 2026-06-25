"""Pipeline pattern app manifest."""

from __future__ import annotations

from palm.common.patterns.app import PatternApp


class PipelineApp(PatternApp):
    name = "pipeline"
    label = "Sequential pipeline"


pipeline_app = PipelineApp()

__all__ = ["PipelineApp", "pipeline_app"]