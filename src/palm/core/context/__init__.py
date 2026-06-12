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
from palm.core.context.observers import StateChangeObserver
from palm.core.context.scoping import NESTED_SCOPES_KEY, SCOPES_ROOT_KEY
from palm.core.context.state_schema import DictStateSchema, StateSchema

__all__ = [
    "BaseState",
    "StateChangeObserver",
    "ContextEngine",
    "DictStateSchema",
    "NESTED_SCOPES_KEY",
    "SCOPES_ROOT_KEY",
    "STATE_FRAME_KEY",
    "STATE_SCOPE_FRAME_KEY",
    "StateSchema",
]
