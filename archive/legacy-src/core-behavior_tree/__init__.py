"""
Palm Behavior Tree Engine – general-purpose, reusable, clean-architecture implementation.

This package provides the foundation for all future Palm orchestration features
(interactive wizards, non-interactive DAGs, agent loops, etc.).

Public API:
- Core types: NodeStatus, Blackboard, BaseNode, RootNode, BehaviorTree
- All concrete nodes (Action, Condition, Sequence, Selector, Parallel, Inverter, Repeat, Retry)
- The InteractiveLeaf extension point
- Domain-agnostic exceptions

This package knows nothing about wizards, RichContext, sessions, or CLI.
"""

from __future__ import annotations

from .base import Blackboard, NodeStatus
from .engine import BehaviorTree
from .exceptions import (
    BehaviorTreeError,
    InvalidTreeStructureError,
    NodeExecutionError,
)
from .nodes.composite.parallel_node import ParallelNode, ParallelPolicy
from .nodes.composite.selector_node import SelectorNode
from .nodes.composite.sequence_node import SequenceNode
from .nodes.decorator.inverter_node import InverterNode
from .nodes.decorator.repeat_node import RepeatNode
from .nodes.decorator.retry_node import RetryNode

# Concrete nodes (convenience re-exports)
from .nodes.leaf.action_node import ActionNode
from .nodes.leaf.condition_node import ConditionNode
from .nodes.leaf.interactive_leaf import InteractiveLeaf
from .root import RootNode

__all__ = [
    # Core
    "NodeStatus",
    "Blackboard",
    "BaseNode",  # re-exported via nodes for completeness
    "RootNode",
    "BehaviorTree",
    # Exceptions
    "BehaviorTreeError",
    "InvalidTreeStructureError",
    "NodeExecutionError",
    # Leaves
    "ActionNode",
    "ConditionNode",
    "InteractiveLeaf",
    # Composites
    "SequenceNode",
    "SelectorNode",
    "ParallelNode",
    "ParallelPolicy",
    # Decorators
    "InverterNode",
    "RepeatNode",
    "RetryNode",
]

# Import BaseNode last so it is available for users who want the ABC
from .base import BaseNode

__all__.append("BaseNode")
