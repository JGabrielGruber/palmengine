"""
Palm Backends — concrete ExecutionBackend implementations for the Orchestration Engine.

This package lives *outside* `palm.core` so that the core Orchestration Engine
remains completely independent of any specific execution technology (Behavior
Trees, subprocesses, remote workers, etc.).

Concrete backends here may depend on domain or peer engines (such as the
Behavior Tree Engine) as needed for composition.

Current contents:
- behavior_tree.py: BehaviorTreeBackend (for running BehaviorTree instances as Jobs)
"""

from __future__ import annotations

__all__ = ["BehaviorTreeBackend"]
