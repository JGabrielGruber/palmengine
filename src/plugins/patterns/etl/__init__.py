"""
ETL pattern app — extract, transform, load pipelines.

Self-contained subpackage: ``pattern.py``, ``builder.py``, ``registry.py``.
"""

from plugins.patterns.etl import registry as registry  # — side effect
from plugins.patterns.etl.pattern import EtlPattern

__all__ = ["EtlPattern", "registry"]
