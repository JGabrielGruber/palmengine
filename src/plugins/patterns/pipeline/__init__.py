"""
Pipeline pattern — declarative transform step sequences.
"""

from plugins.patterns.pipeline import registry as registry  # — side effect
from plugins.patterns.pipeline.bindings.definitions.config import PipelineConfig
from plugins.patterns.pipeline.pattern import PipelinePattern

__all__ = ["PipelineConfig", "PipelinePattern", "registry"]
