"""
Optional integration test proving that the Orchestration Engine composes cleanly
with the Behavior Tree Engine via BehaviorTreeBackend.

THIS IS THE ONLY TEST FILE IN THE ORCHESTRATION SUITE ALLOWED TO IMPORT
FROM palm.core.behavior_tree (for the tree construction itself).

The BehaviorTreeBackend is imported from its proper home: `palm.backends.behavior_tree`.

All other tests must stay 100% independent and use only TestBackend.
"""

from __future__ import annotations

from palm.backends.behavior_tree import BehaviorTreeBackend
from palm.core.behavior_tree import (
    ActionNode,
    BehaviorTree,
    NodeStatus,
    RootNode,
)
from palm.core.orchestration import (
    JobStatus,
    Orchestrator,
    TestMode,
)


def test_orchestrator_can_run_real_behavior_tree_via_backend() -> None:
    """
    End-to-end: submit a real BehaviorTree as a job using the optional
    BehaviorTreeBackend through TestMode.
    """
    backend = BehaviorTreeBackend()
    mode = TestMode(backend=backend)

    orch = Orchestrator(mode=mode)
    orch.start()

    # Build a tiny successful tree
    def set_done(bb):
        bb.set("done", True)
        return NodeStatus.SUCCESS

    action = ActionNode("mark_done", action=lambda bb: (set_done(bb) or NodeStatus.SUCCESS))
    root = RootNode("root", child=action)
    tree = BehaviorTree(root)

    job = orch.submit(tree)

    assert job.status == JobStatus.SUCCEEDED
    # The BehaviorTree owns its blackboard; the Job re-uses it for BT backends
    assert tree.blackboard.get("done") is True

    orch.shutdown()
