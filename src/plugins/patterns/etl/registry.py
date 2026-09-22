"""ETL pattern registration — import this module to wire the app."""

from palm.common.patterns._registry import register_builder
from palm.core.registry import pattern_registry
from plugins.patterns.etl.app import etl_app
from plugins.patterns.etl.bindings.definitions.builder import build
from plugins.patterns.etl.pattern import EtlPattern

pattern_registry.register("etl", EtlPattern)
register_builder("etl", build)
etl_app.register()
