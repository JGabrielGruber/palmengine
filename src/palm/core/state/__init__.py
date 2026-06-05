"""
State abstractions — pluggable execution state for engines and patterns.

Pure core module: no imports from outside ``palm.core``.
"""

from palm.core.state.base_state import BaseState

# Context frame key for attaching a BaseState instance
STATE_FRAME_KEY = "state"

__all__ = ["BaseState", "STATE_FRAME_KEY"]