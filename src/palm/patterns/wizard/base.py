"""
Wizard pattern foundation — extends core behavior tree primitives.

Wizard nodes and leaves build on ``BasePattern`` from ``palm.core``; this module
documents the contract for the wizard app without duplicating core types.
"""

from palm.core.behavior_tree import BasePattern, PatternStatus

__all__ = ["BasePattern", "PatternStatus"]