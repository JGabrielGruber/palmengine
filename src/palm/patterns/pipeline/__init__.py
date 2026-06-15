"""
Pipeline pattern — declarative transform step sequences.

Self-contained subpackage: ``pattern.py``, ``builder.py``, ``registry.py``.
"""

from palm.patterns.pipeline import registry as registry  # — side effect
from palm.patterns.pipeline.config import PipelineConfig
from palm.patterns.pipeline.pattern import PipelinePattern

__all__ = ["PipelineConfig", "PipelinePattern", "registry"]
