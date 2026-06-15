"""
Transform rule registry — thread-safe name → rule class map.
"""

from __future__ import annotations

from palm.core.registry import Registry
from palm.core.transform.base import BaseTransformRule

transform_registry: Registry[BaseTransformRule] = Registry("transform")
