"""
Context engine — scoped execution metadata and pluggable state.

Pure core module: no imports from outside ``palm.core``.
"""

from palm.core.context.base_state import BaseState
from palm.core.context.engine import (
    STATE_FRAME_KEY,
    STATE_SCOPE_FRAME_KEY,
    ContextEngine,
)
from palm.core.context.state_schema import DictStateSchema, StateSchema

__all__ = [
    "BaseState",
    "ContextEngine",
    "DictStateSchema",
    "STATE_FRAME_KEY",
    "STATE_SCOPE_FRAME_KEY",
    "StateSchema",
]
