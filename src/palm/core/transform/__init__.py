"""
Transform engine — register and apply data transformation rules.

Core defines the engine contract and registry. Concrete rule implementations
belong in ``palm.common.transforms`` and pattern packages (outside core).
"""

from palm.core.transform.base import (
    BaseTransformRule,
    TransformContext,
    TransformFrame,
    TransformMode,
    TransformResult,
)
from palm.core.transform.engine import TransformEngine
from palm.core.transform.registry import transform_registry

__all__ = [
    "BaseTransformRule",
    "TransformContext",
    "TransformEngine",
    "TransformFrame",
    "TransformMode",
    "TransformResult",
    "transform_registry",
]
