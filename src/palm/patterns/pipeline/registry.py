"""Pipeline pattern registration."""

from palm.core.registry import pattern_registry
from palm.patterns._registry import register_builder
from palm.patterns.pipeline.app import pipeline_app
from palm.patterns.pipeline.builder import build
from palm.patterns.pipeline.pattern import PipelinePattern

pattern_registry.register("pipeline", PipelinePattern)
register_builder("pipeline", build)
pipeline_app.register()
