"""
Behavior Tree engine exceptions.

Pure core module: no imports from outside ``palm.core``.
"""

from __future__ import annotations

from palm.core.exceptions import PalmError


class BehaviorTreeError(PalmError):
    """Base exception for behavior tree failures."""


class InvalidTreeStructureError(BehaviorTreeError):
    """Raised when tree construction or validation fails."""


class NodeExecutionError(BehaviorTreeError):
    """Raised when a node tick fails unexpectedly."""