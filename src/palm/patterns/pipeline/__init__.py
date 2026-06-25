"""
Pipeline pattern — declarative transform step sequences.
"""

from palm.patterns.pipeline import registry as registry  # — side effect
from palm.patterns.pipeline.bindings.definitions.config import PipelineConfig
from palm.patterns.pipeline.pattern import PipelinePattern

__all__ = ["PipelineConfig", "PipelinePattern", "registry"]