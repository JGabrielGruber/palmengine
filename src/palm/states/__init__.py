"""
Concrete state implementations for Palm engines and patterns.

Register or construct these outside ``palm.core`` and pass into engines via
``initialize(state=...)``.
"""

from palm.states.blackboard_state import BlackboardState
from palm.states.recording_state import RecordingState

# Public alias for tests and examples
TestState = RecordingState

__all__ = ["BlackboardState", "RecordingState", "TestState"]