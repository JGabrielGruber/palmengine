"""Pipeline pattern registration."""

from palm.common.patterns._registry import register_builder
from palm.core.registry import pattern_registry
from plugins.patterns.pipeline.app import pipeline_app
from plugins.patterns.pipeline.bindings.definitions.builder import build
from plugins.patterns.pipeline.pattern import PipelinePattern

pattern_registry.register("pipeline", PipelinePattern)
register_builder("pipeline", build)
pipeline_app.register()
