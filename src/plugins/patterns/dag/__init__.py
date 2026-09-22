"""
DAG pattern app — directed acyclic workflow execution.

Self-contained subpackage: ``pattern.py``, ``builder.py``, ``registry.py``.
"""

from plugins.patterns.dag import registry as registry  # — side effect
from plugins.patterns.dag.pattern import DagPattern

__all__ = ["DagPattern", "registry"]
