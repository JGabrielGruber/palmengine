"""
End-to-end integration tests exercising mixed node types, the full public API,
reset semantics, WAITING_FOR_INPUT, and the exact "guaranteed working example"
published in the implementation plan.
"""

from __future__ import annotations

from palm.core.behavior_tree import (
    ActionNode,
    BehaviorTree,
    Blackboard,
    ConditionNode,
    InverterNode,
    NodeStatus,
    RootNode,
    SelectorNode,
    SequenceNode,
)
from palm.core.behavior_tree.nodes.leaf.interactive_leaf import _TestInteractiveLeaf


def build_example_tree() -> RootNode:
    """Exact tree from the approved implementation plan."""

    def mark_done(bb: Blackboard) -> None:
        bb.set("work_done", True)

    def is_done(bb: Blackboard) -> bool:
        return bb.get("work_done", False)

    work_seq = SequenceNode(
        "do_work",
        children=[
            ConditionNode("not_done_yet", predicate=lambda bb: not is_done(bb)),
            ActionNode("perform_work", action=lambda bb: (mark_done(bb) or NodeStatus.SUCCESS)),
        ],
    )

    verify = SequenceNode(
        "verify",
        children=[
            ConditionNode("check_done", predicate=is_done),
            InverterNode(
                "should_not_be_here", child=ConditionNode("fail_if_reached", lambda bb: False)
            ),
        ],
    )

    root_logic = SelectorNode("main_fallback", children=[verify, work_seq])
    return RootNode("root", child=root_logic)


def test_guaranteed_working_example_from_plan() -> None:
    """This test MUST pass. It is the contract example for the whole engine."""
    tree = BehaviorTree(build_example_tree())
    bb = tree.blackboard

    status = tree.tick_until_terminal()
    assert status == NodeStatus.SUCCESS
    assert bb.get("work_done") is True

    tree.reset()
    status2 = tree.tick_until_terminal()
    assert status2 == NodeStatus.SUCCESS
    # The verify branch should have short-circuited; side effect not re-executed
    # (the counter is not tracked here, but the logic is exercised)


def test_waiting_for_input_propagates_correctly() -> None:
    interactive = _TestInteractiveLeaf("ask_name")
    root = RootNode("root", child=interactive)
    tree = BehaviorTree(root)

    status = tree.tick()
    assert status == NodeStatus.WAITING_FOR_INPUT

    # Simulate UI supplying the answer via the documented convention
    key = interactive.input_key()
    tree.blackboard.set(key, "Grace Hopper")

    status2 = tree.tick()
    assert status2 == NodeStatus.SUCCESS
    assert interactive.received_value == "Grace Hopper"


def test_deep_nesting_does_not_explode_recursion() -> None:
    """Smoke test that 50 levels of nesting is still fine (real limit is much higher)."""
    node: RootNode | SequenceNode = RootNode(
        "deep_root", child=ConditionNode("leaf", lambda bb: True)
    )
    for i in range(50):
        node = SequenceNode(f"level_{i}", children=[node])  # type: ignore[assignment]

    # Wrap the final sequence in a proper RootNode if needed
    if not isinstance(node, RootNode):
        node = RootNode("final_root", child=node)  # type: ignore[arg-type]

    tree = BehaviorTree(node)
    assert tree.tick_until_terminal() == NodeStatus.SUCCESS


def test_blackboard_isolation_between_resets() -> None:
    bb = Blackboard()
    action = ActionNode("writer", action=lambda b: (b.set("x", 1) or NodeStatus.SUCCESS))
    tree = BehaviorTree(RootNode("r", child=action), blackboard=bb)

    tree.tick_until_terminal()
    assert bb.get("x") == 1

    tree.reset()
    # The blackboard is intentionally *not* cleared by tree.reset()
    # (that is a deliberate design choice – caller owns data lifetime)
    assert bb.get("x") == 1
