"""
Workflow subsystem (non-interactive DAG execution).

Currently lightweight scaffolding. Future home of pure DAG workflows
that do not require interactive pauses.
"""

from .dag import DAG, Node
from .executor import WorkflowExecutor
from .registry import WorkflowRegistry

__all__ = ["DAG", "Node", "WorkflowExecutor", "WorkflowRegistry"]
