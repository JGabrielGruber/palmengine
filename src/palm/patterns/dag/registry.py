"""DAG pattern registration — import this module to wire the app."""

from palm.core.registry import pattern_registry
from palm.patterns._registry import register_builder
from palm.patterns.dag.app import dag_app
from palm.patterns.dag.builder import build
from palm.patterns.dag.pattern import DagPattern

pattern_registry.register("dag", DagPattern)
register_builder("dag", build)
dag_app.register()
