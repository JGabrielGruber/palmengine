"""
Transform engine — register and apply data transformation rules.

Core ships minimal primitives (rename, pick, filter, map, format). Rich rule
libraries belong in ``palm.common.transforms`` (outside core).
"""

from palm.core.transform.base_transform import BaseTransform
from palm.core.transform.context import TransformContext, TransformFrame, TransformMode
from palm.core.transform.engine import TransformEngine
from palm.core.transform.exceptions import TransformApplicationError, TransformError
from palm.core.transform.primitives import register_core_transforms

__all__ = [
    "BaseTransform",
    "TransformApplicationError",
    "TransformContext",
    "TransformEngine",
    "TransformError",
    "TransformFrame",
    "TransformMode",
    "register_core_transforms",
]