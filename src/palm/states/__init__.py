"""
Concrete state implementations for Palm engines and patterns.

Register or construct these outside ``palm.core`` and pass into engines via
``initialize(state=...)``.
"""

from palm.states.blackboard_state import BlackboardState

__all__ = ["BlackboardState"]