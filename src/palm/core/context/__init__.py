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
from palm.core.context.scoping import (
    LEGACY_SCOPE_PREFIX,
    NESTED_SCOPES_KEY,
    SCOPES_ROOT_KEY,
    legacy_storage_key,
)
from palm.core.context.state_schema import DictStateSchema, StateSchema

__all__ = [
    "BaseState",
    "ContextEngine",
    "DictStateSchema",
    "LEGACY_SCOPE_PREFIX",
    "NESTED_SCOPES_KEY",
    "SCOPES_ROOT_KEY",
    "legacy_storage_key",
    "STATE_FRAME_KEY",
    "STATE_SCOPE_FRAME_KEY",
    "StateSchema",
]
