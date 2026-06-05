"""
Context engine — scoped execution metadata and pluggable state.

Pure core module: no imports from outside ``palm.core``.
"""

from palm.core.context.base_state import BaseState
from palm.core.context.engine import STATE_FRAME_KEY, ContextEngine

__all__ = ["BaseState", "ContextEngine", "STATE_FRAME_KEY"]