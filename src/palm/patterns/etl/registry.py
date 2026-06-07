"""ETL pattern registration — import this module to wire the app."""

from palm.core.registry import pattern_registry
from palm.patterns._registry import register_builder
from palm.patterns.etl.builder import build
from palm.patterns.etl.pattern import EtlPattern

pattern_registry.register("etl", EtlPattern)
register_builder("etl", build)