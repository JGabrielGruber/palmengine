"""Comprehensive tests for behavior tree composite and decorator nodes."""

from __future__ import annotations

from collections.abc import Callable

import pytest

from palm.core.behavior_tree import (
    ActionNode,
    BaseNode,
    ConditionNode,
    InvalidTreeStructureError,
    InverterNode,
    LeafNode,
    NodeExecutionError,
    ParallelNode,
    ParallelPolicy,
    PatternStatus,
    RepeatNode,
    RetryNode,
    RootNode,
    SelectorNode,
    SequenceNode,
)
from palm.core.behavior_tree.exceptions import BehaviorTreeError
from palm.core.context import BaseState
from tests.core.fakes import StubInteractiveLeaf, TestState


def _action(
    name: str,
    fn: Callable[[BaseState], PatternStatus | None],
) -> ActionNode:
    return ActionNode(name, action=fn)


def _status_action(name: str, status: PatternStatus) -> ActionNode:
    return _action(name, lambda _s: status)


def _counting_action(name: str, counter: dict[str, int]) -> ActionNode:
    def tick(_s: BaseState) -> PatternStatus:
        counter[name] = counter.get(name, 0) + 1
        return PatternStatus.SUCCESS

    return _action(name, tick)


# --- SequenceNode ---


def test_sequence_empty_children_succeeds(test_state: TestState) -> None:
    assert SequenceNode("empty").tick(test_state) == PatternStatus.SUCCESS


def test_sequence_runs_all_children_in_order(test_state: TestState) -> None:
    order: list[str] = []

    def record(name: str) -> ActionNode:
        return _action(name, lambda _s: order.append(name) or PatternStatus.SUCCESS)

    node = SequenceNode(
        "seq",
        children=[record("a"), record("b"), record("c")],
    )
    assert node.tick(test_state) == PatternStatus.SUCCESS
    assert order == ["a", "b", "c"]


def test_sequence_stops_on_first_failure_and_resets_index(test_state: TestState) -> None:
    calls: list[str] = []

    def track(name: str, status: PatternStatus) -> ActionNode:
        return _action(
            name,
            lambda _s: calls.append(name) or status,
        )

    node = SequenceNode(
        "seq",
        children=[
            track("ok", PatternStatus.SUCCESS),
            track("fail", PatternStatus.FAILURE),
            track("skipped", PatternStatus.SUCCESS),
        ],
    )
    assert node.tick(test_state) == PatternStatus.FAILURE
    assert calls == ["ok", "fail"]

    calls.clear()
    assert node.tick(test_state) == PatternStatus.FAILURE
    assert calls == ["ok", "fail"]


def test_sequence_returns_running_and_resumes_at_same_child(test_state: TestState) -> None:
    ticks = {"n": 0}
    calls: list[str] = []

    def step(_s: BaseState) -> PatternStatus:
        calls.append("step")
        ticks["n"] += 1
        return PatternStatus.RUNNING if ticks["n"] < 2 else PatternStatus.SUCCESS

    node = SequenceNode(
        "seq",
        children=[
            _action("before", lambda _s: calls.append("before") or PatternStatus.SUCCESS),
            _action("step", step),
            _action("after", lambda _s: calls.append("after") or PatternStatus.SUCCESS),
        ],
    )
    assert node.tick(test_state) == PatternStatus.RUNNING
    assert calls == ["before", "step"]

    assert node.tick(test_state) == PatternStatus.SUCCESS
    assert calls == ["before", "step", "step", "after"]


def test_sequence_returns_waiting_for_input(test_state: TestState) -> None:
    calls: list[str] = []
    leaf = StubInteractiveLeaf("ask")

    node = SequenceNode(
        "seq",
        children=[
            _action("before", lambda _s: calls.append("before") or PatternStatus.SUCCESS),
            leaf,
            _action("after", lambda _s: calls.append("after") or PatternStatus.SUCCESS),
        ],
    )
    assert node.tick(test_state) == PatternStatus.WAITING_FOR_INPUT
    assert calls == ["before"]
    assert test_state.get(leaf.prompt_key()) == {"message": "Please provide input"}

    test_state.set(leaf.input_key(), "yes")
    assert node.tick(test_state) == PatternStatus.SUCCESS
    assert calls == ["before", "after"]
    assert leaf.received_value == "yes"


def test_sequence_reset_restarts_from_first_child(test_state: TestState) -> None:
    index = {"n": 0}

    def alternating(_s: BaseState) -> PatternStatus:
        index["n"] += 1
        return PatternStatus.SUCCESS if index["n"] % 2 == 1 else PatternStatus.FAILURE

    node = SequenceNode("seq", children=[_action("alt", alternating)])

    assert node.tick(test_state) == PatternStatus.SUCCESS
    assert node.tick(test_state) == PatternStatus.FAILURE

    node.reset()
    index["n"] = 0
    assert node.tick(test_state) == PatternStatus.SUCCESS


# --- SelectorNode ---


def test_selector_empty_children_fails(test_state: TestState) -> None:
    assert SelectorNode("empty").tick(test_state) == PatternStatus.FAILURE


def test_selector_succeeds_on_first_successful_child(test_state: TestState) -> None:
    calls: list[str] = []

    def track(name: str, result: bool) -> ConditionNode:
        def pred(_s: BaseState) -> bool:
            calls.append(name)
            return result

        return ConditionNode(name, pred)

    node = SelectorNode(
        "sel",
        children=[
            track("fail", False),
            track("ok", True),
            track("skipped", True),
        ],
    )
    assert node.tick(test_state) == PatternStatus.SUCCESS
    assert calls == ["fail", "ok"]


def test_selector_fails_when_all_children_fail(test_state: TestState) -> None:
    node = SelectorNode(
        "sel",
        children=[
            ConditionNode("a", lambda _s: False),
            ConditionNode("b", lambda _s: False),
        ],
    )
    assert node.tick(test_state) == PatternStatus.FAILURE


def test_selector_returns_running_and_resumes_at_same_child(test_state: TestState) -> None:
    ticks = {"n": 0}
    calls: list[str] = []

    def step(_s: BaseState) -> PatternStatus:
        calls.append("step")
        ticks["n"] += 1
        return PatternStatus.RUNNING if ticks["n"] < 2 else PatternStatus.SUCCESS

    node = SelectorNode(
        "sel",
        children=[
            ConditionNode("fail", lambda _s: False),
            _action("step", step),
            _action("after", lambda _s: calls.append("after") or PatternStatus.SUCCESS),
        ],
    )
    assert node.tick(test_state) == PatternStatus.RUNNING
    assert calls == ["step"]

    assert node.tick(test_state) == PatternStatus.SUCCESS
    assert calls == ["step", "step"]
    assert "after" not in calls


def test_selector_returns_waiting_for_input(test_state: TestState) -> None:
    leaf = StubInteractiveLeaf("ask")
    node = SelectorNode(
        "sel",
        children=[
            ConditionNode("fail", lambda _s: False),
            leaf,
        ],
    )
    assert node.tick(test_state) == PatternStatus.WAITING_FOR_INPUT

    test_state.set(leaf.input_key(), "value")
    assert node.tick(test_state) == PatternStatus.SUCCESS


def test_selector_reset_restarts_from_first_child(test_state: TestState) -> None:
    index = {"n": 0}

    def alternating(_s: BaseState) -> PatternStatus:
        index["n"] += 1
        return PatternStatus.SUCCESS if index["n"] == 2 else PatternStatus.FAILURE

    node = SelectorNode("sel", children=[_action("alt", alternating)])

    assert node.tick(test_state) == PatternStatus.FAILURE
    assert node.tick(test_state) == PatternStatus.SUCCESS

    node.reset()
    index["n"] = 0
    assert node.tick(test_state) == PatternStatus.FAILURE


# --- ParallelNode ---


def test_parallel_empty_children_succeeds(test_state: TestState) -> None:
    assert ParallelNode("empty").tick(test_state) == PatternStatus.SUCCESS


def test_parallel_success_on_all_requires_every_child(test_state: TestState) -> None:
    counter: dict[str, int] = {}
    node = ParallelNode(
        "parallel",
        children=[
            _counting_action("a", counter),
            _counting_action("b", counter),
        ],
        policy=ParallelPolicy.SUCCESS_ON_ALL,
    )
    assert node.tick(test_state) == PatternStatus.SUCCESS
    assert counter == {"a": 1, "b": 1}


def test_parallel_success_on_all_fails_on_first_failure(test_state: TestState) -> None:
    counter: dict[str, int] = {}
    node = ParallelNode(
        "parallel",
        children=[
            _counting_action("ok", counter),
            _status_action("fail", PatternStatus.FAILURE),
            _counting_action("skipped", counter),
        ],
        policy=ParallelPolicy.SUCCESS_ON_ALL,
    )
    assert node.tick(test_state) == PatternStatus.FAILURE
    assert "ok" in counter
    assert "skipped" not in counter


def test_parallel_success_on_any_short_circuits_on_success(test_state: TestState) -> None:
    counter: dict[str, int] = {}
    node = ParallelNode(
        "parallel",
        children=[
            _status_action("win", PatternStatus.SUCCESS),
            _status_action("lose", PatternStatus.FAILURE),
            _counting_action("never", counter),
        ],
        policy=ParallelPolicy.SUCCESS_ON_ANY,
    )
    assert node.tick(test_state) == PatternStatus.SUCCESS
    assert "never" not in counter


def test_parallel_success_on_any_fails_when_all_fail(test_state: TestState) -> None:
    node = ParallelNode(
        "parallel",
        children=[
            _status_action("a", PatternStatus.FAILURE),
            _status_action("b", PatternStatus.FAILURE),
        ],
        policy=ParallelPolicy.SUCCESS_ON_ANY,
    )
    assert node.tick(test_state) == PatternStatus.FAILURE


def test_parallel_mixed_running_then_success_on_all(test_state: TestState) -> None:
    ticks = {"a": 0, "b": 0}

    def run_twice(name: str) -> Callable[[BaseState], PatternStatus]:
        def tick(_s: BaseState) -> PatternStatus:
            ticks[name] += 1
            return PatternStatus.RUNNING if ticks[name] < 2 else PatternStatus.SUCCESS

        return tick

    node = ParallelNode(
        "parallel",
        children=[
            _action("a", run_twice("a")),
            _action("b", run_twice("b")),
        ],
        policy=ParallelPolicy.SUCCESS_ON_ALL,
    )
    assert node.tick(test_state) == PatternStatus.RUNNING
    assert node.tick(test_state) == PatternStatus.SUCCESS


def test_parallel_waiting_for_input_beats_running(test_state: TestState) -> None:
    leaf = StubInteractiveLeaf("ask")
    node = ParallelNode(
        "parallel",
        children=[
            _status_action("running", PatternStatus.RUNNING),
            leaf,
        ],
        policy=ParallelPolicy.SUCCESS_ON_ALL,
    )
    assert node.tick(test_state) == PatternStatus.WAITING_FOR_INPUT


def test_parallel_skips_terminal_children_on_subsequent_ticks(test_state: TestState) -> None:
    ticks = {"slow": 0}
    counter = {"fast": 0}

    def fast(_s: BaseState) -> PatternStatus:
        counter["fast"] += 1
        return PatternStatus.SUCCESS

    def slow(_s: BaseState) -> PatternStatus:
        ticks["slow"] += 1
        return PatternStatus.RUNNING if ticks["slow"] < 2 else PatternStatus.SUCCESS

    node = ParallelNode(
        "parallel",
        children=[
            _action("fast", fast),
            _action("slow", slow),
        ],
        policy=ParallelPolicy.SUCCESS_ON_ALL,
    )
    assert node.tick(test_state) == PatternStatus.RUNNING
    assert counter["fast"] == 1
    assert ticks["slow"] == 1

    assert node.tick(test_state) == PatternStatus.SUCCESS
    assert counter["fast"] == 1
    assert ticks["slow"] == 2


def test_parallel_success_on_any_succeeds_when_one_child_eventually_wins(
    test_state: TestState,
) -> None:
    ticks = {"slow": 0}
    counter = {"fast": 0}

    def fast(_s: BaseState) -> PatternStatus:
        counter["fast"] += 1
        return PatternStatus.FAILURE

    def slow(_s: BaseState) -> PatternStatus:
        ticks["slow"] += 1
        return PatternStatus.RUNNING if ticks["slow"] < 2 else PatternStatus.SUCCESS

    node = ParallelNode(
        "parallel",
        children=[_action("fast", fast), _action("slow", slow)],
        policy=ParallelPolicy.SUCCESS_ON_ANY,
    )
    assert node.tick(test_state) == PatternStatus.RUNNING
    assert counter["fast"] == 1

    assert node.tick(test_state) == PatternStatus.SUCCESS
    assert ticks["slow"] == 2


def test_parallel_reset_clears_cached_child_results(test_state: TestState) -> None:
    attempts = {"n": 0}

    def once(_s: BaseState) -> PatternStatus:
        attempts["n"] += 1
        return PatternStatus.SUCCESS if attempts["n"] == 1 else PatternStatus.FAILURE

    node = ParallelNode(
        "parallel",
        children=[_action("once", once)],
        policy=ParallelPolicy.SUCCESS_ON_ALL,
    )
    assert node.tick(test_state) == PatternStatus.SUCCESS
    assert node.tick(test_state) == PatternStatus.SUCCESS

    node.reset()
    attempts["n"] = 0
    assert node.tick(test_state) == PatternStatus.SUCCESS


# --- InverterNode ---


@pytest.mark.parametrize(
    ("child_status", "expected"),
    [
        (PatternStatus.SUCCESS, PatternStatus.FAILURE),
        (PatternStatus.FAILURE, PatternStatus.SUCCESS),
        (PatternStatus.RUNNING, PatternStatus.RUNNING),
        (PatternStatus.WAITING_FOR_INPUT, PatternStatus.WAITING_FOR_INPUT),
    ],
)
def test_inverter_flips_terminal_statuses_only(
    test_state: TestState,
    child_status: PatternStatus,
    expected: PatternStatus,
) -> None:
    node = InverterNode("inv", child=_status_action("child", child_status))
    assert node.tick(test_state) == expected


# --- RepeatNode ---


def test_repeat_fixed_times_succeeds(test_state: TestState) -> None:
    counter = {"n": 0}
    node = RepeatNode(
        "repeat",
        child=_action(
            "body", lambda _s: counter.update({"n": counter["n"] + 1}) or PatternStatus.SUCCESS
        ),
        times=3,
    )
    assert node.tick(test_state) == PatternStatus.SUCCESS
    assert counter["n"] == 3


def test_repeat_unbounded_until_failure(test_state: TestState) -> None:
    counter = {"n": 0}

    def body(_s: BaseState) -> PatternStatus:
        counter["n"] += 1
        return PatternStatus.FAILURE if counter["n"] == 4 else PatternStatus.SUCCESS

    node = RepeatNode("repeat", child=_action("body", body), times=None)
    assert node.tick(test_state) == PatternStatus.FAILURE
    assert counter["n"] == 4


def test_repeat_failure_resets_count(test_state: TestState) -> None:
    counter = {"n": 0}
    fail_once = {"remaining": 1}

    def body(_s: BaseState) -> PatternStatus:
        counter["n"] += 1
        if fail_once["remaining"] > 0:
            fail_once["remaining"] -= 1
            return PatternStatus.FAILURE
        return PatternStatus.SUCCESS

    node = RepeatNode("repeat", child=_action("body", body), times=2)
    assert node.tick(test_state) == PatternStatus.FAILURE
    assert counter["n"] == 1

    assert node.tick(test_state) == PatternStatus.SUCCESS
    assert counter["n"] == 3


def test_repeat_propagates_running(test_state: TestState) -> None:
    ticks = {"n": 0}

    def body(_s: BaseState) -> PatternStatus:
        ticks["n"] += 1
        return PatternStatus.RUNNING if ticks["n"] < 2 else PatternStatus.SUCCESS

    node = RepeatNode("repeat", child=_action("body", body), times=2)
    assert node.tick(test_state) == PatternStatus.RUNNING
    assert node.tick(test_state) == PatternStatus.SUCCESS


def test_repeat_propagates_waiting_for_input(test_state: TestState) -> None:
    leaf = StubInteractiveLeaf("ask")
    node = RepeatNode("repeat", child=leaf, times=1)
    assert node.tick(test_state) == PatternStatus.WAITING_FOR_INPUT

    test_state.set(leaf.input_key(), "ok")
    assert node.tick(test_state) == PatternStatus.SUCCESS


def test_repeat_rejects_invalid_times() -> None:
    child = _status_action("child", PatternStatus.SUCCESS)
    with pytest.raises(ValueError, match="times must be None or >= 1"):
        RepeatNode("repeat", child=child, times=0)


def test_repeat_reset_clears_count(test_state: TestState) -> None:
    counter = {"n": 0}
    node = RepeatNode(
        "repeat",
        child=_action(
            "body", lambda _s: counter.update({"n": counter["n"] + 1}) or PatternStatus.SUCCESS
        ),
        times=2,
    )
    assert node.tick(test_state) == PatternStatus.SUCCESS
    assert counter["n"] == 2

    node.reset()
    counter["n"] = 0
    assert node.tick(test_state) == PatternStatus.SUCCESS
    assert counter["n"] == 2


# --- RetryNode ---


def test_retry_succeeds_on_first_attempt(test_state: TestState) -> None:
    counter = {"n": 0}
    node = RetryNode(
        "retry",
        child=_action(
            "body", lambda _s: counter.update({"n": counter["n"] + 1}) or PatternStatus.SUCCESS
        ),
        max_attempts=3,
    )
    assert node.tick(test_state) == PatternStatus.SUCCESS
    assert counter["n"] == 1


def test_retry_retries_until_success(test_state: TestState) -> None:
    counter = {"n": 0}

    def body(_s: BaseState) -> PatternStatus:
        counter["n"] += 1
        return PatternStatus.SUCCESS if counter["n"] == 3 else PatternStatus.FAILURE

    node = RetryNode("retry", child=_action("body", body), max_attempts=5)
    assert node.tick(test_state) == PatternStatus.SUCCESS
    assert counter["n"] == 3


def test_retry_fails_after_max_attempts(test_state: TestState) -> None:
    counter = {"n": 0}
    node = RetryNode(
        "retry",
        child=_action(
            "body", lambda _s: counter.update({"n": counter["n"] + 1}) or PatternStatus.FAILURE
        ),
        max_attempts=3,
    )
    assert node.tick(test_state) == PatternStatus.FAILURE
    assert counter["n"] == 3


def test_retry_propagates_running_without_consuming_attempt(test_state: TestState) -> None:
    ticks = {"n": 0}

    def body(_s: BaseState) -> PatternStatus:
        ticks["n"] += 1
        return PatternStatus.RUNNING if ticks["n"] < 2 else PatternStatus.SUCCESS

    node = RetryNode("retry", child=_action("body", body), max_attempts=3)
    assert node.tick(test_state) == PatternStatus.RUNNING
    assert node.tick(test_state) == PatternStatus.SUCCESS
    assert ticks["n"] == 2


def test_retry_propagates_waiting_for_input(test_state: TestState) -> None:
    leaf = StubInteractiveLeaf("ask")
    node = RetryNode("retry", child=leaf, max_attempts=3)
    assert node.tick(test_state) == PatternStatus.WAITING_FOR_INPUT

    test_state.set(leaf.input_key(), "ok")
    assert node.tick(test_state) == PatternStatus.SUCCESS


def test_retry_rejects_invalid_max_attempts() -> None:
    child = _status_action("child", PatternStatus.SUCCESS)
    with pytest.raises(ValueError, match="max_attempts must be >= 1"):
        RetryNode("retry", child=child, max_attempts=0)


def test_retry_reset_clears_attempts(test_state: TestState) -> None:
    counter = {"n": 0}

    def body(_s: BaseState) -> PatternStatus:
        counter["n"] += 1
        return PatternStatus.FAILURE

    node = RetryNode("retry", child=_action("body", body), max_attempts=2)
    assert node.tick(test_state) == PatternStatus.FAILURE
    assert counter["n"] == 2

    node.reset()
    counter["n"] = 0
    assert node.tick(test_state) == PatternStatus.FAILURE
    assert counter["n"] == 2


# --- Tree structure validation ---


def test_add_child_rejects_node_that_already_has_parent() -> None:
    parent_a = SequenceNode("a")
    parent_b = SequenceNode("b")
    child = _status_action("child", PatternStatus.SUCCESS)
    parent_a._add_child(child)

    with pytest.raises(InvalidTreeStructureError, match="already has parent"):
        parent_b._add_child(child)


def test_add_child_detects_direct_cycle() -> None:
    parent = SequenceNode("parent")
    child = SequenceNode("child")
    parent._add_child(child)

    with pytest.raises(InvalidTreeStructureError, match="Cycle detected"):
        child._add_child(parent)


def test_add_child_detects_indirect_cycle() -> None:
    root = SequenceNode("root")
    mid = SequenceNode("mid")
    leaf = SequenceNode("leaf")
    root._add_child(mid)
    mid._add_child(leaf)

    with pytest.raises(InvalidTreeStructureError, match="Cycle detected"):
        leaf._add_child(root)


def test_leaf_node_rejects_children() -> None:
    leaf = _status_action("leaf", PatternStatus.SUCCESS)
    with pytest.raises(InvalidTreeStructureError, match="cannot have children"):
        leaf._add_child(_status_action("child", PatternStatus.SUCCESS))


def test_decorator_rejects_second_child() -> None:
    first = _status_action("first", PatternStatus.SUCCESS)
    second = _status_action("second", PatternStatus.SUCCESS)
    inverter = InverterNode("inv", child=first)

    with pytest.raises(InvalidTreeStructureError, match="already has child"):
        inverter._add_child(second)


def test_decorator_child_property_requires_child() -> None:
    node = InverterNode.__new__(InverterNode)
    BaseNode.__init__(node, "bare")

    with pytest.raises(InvalidTreeStructureError, match="has no child"):
        _ = node.child


def test_composite_validate_child_count_requires_children() -> None:
    node = SequenceNode("empty")
    with pytest.raises(InvalidTreeStructureError, match="must have at least one child"):
        node._validate_child_count()


def test_decorator_validate_child_count_requires_exactly_one_child() -> None:
    node = InverterNode.__new__(InverterNode)
    BaseNode.__init__(node, "bare")

    with pytest.raises(InvalidTreeStructureError, match="must have exactly one child"):
        node._validate_child_count()


def test_validate_tree_structure_detects_duplicate_node_reference() -> None:
    child = _status_action("shared", PatternStatus.SUCCESS)
    parent = SequenceNode("parent")
    parent.children.append(child)
    parent.children.append(child)
    child.parent = parent

    with pytest.raises(InvalidTreeStructureError, match="Duplicate node or cycle"):
        parent.validate_tree_structure()


def test_root_node_validates_on_construction() -> None:
    child = _status_action("child", PatternStatus.SUCCESS)
    parent = SequenceNode("parent")
    parent.children.append(child)
    parent.children.append(child)
    child.parent = parent

    with pytest.raises(InvalidTreeStructureError):
        RootNode("root", child=parent)


# --- Error handling ---


def test_node_execution_error_on_unhandled_exception(test_state: TestState) -> None:
    def boom(_s: BaseState) -> PatternStatus:
        raise RuntimeError("boom")

    node = _action("boom", boom)
    with pytest.raises(NodeExecutionError, match="Unhandled exception"):
        node.tick(test_state)


def test_node_execution_error_on_non_pattern_status_return(test_state: TestState) -> None:
    class BadLeaf(LeafNode):
        def _tick_impl(self, state: BaseState) -> PatternStatus:
            return "not-a-status"  # type: ignore[return-value]

    node = BadLeaf("bad")
    with pytest.raises(NodeExecutionError, match="non-PatternStatus"):
        node.tick(test_state)


def test_action_node_maps_unknown_return_to_failure(test_state: TestState) -> None:
    node = _action("bad", lambda _s: "not-a-status")  # type: ignore[return-value]
    assert node.tick(test_state) == PatternStatus.FAILURE


def test_base_node_repr_includes_children() -> None:
    node = SequenceNode(
        "seq",
        children=[
            _status_action("a", PatternStatus.SUCCESS),
            _status_action("b", PatternStatus.SUCCESS),
        ],
    )
    assert repr(node) == "SequenceNode(name='seq', children=['a', 'b'])"


def test_behavior_tree_error_propagates_without_wrapping(test_state: TestState) -> None:
    class CustomBehaviorTreeError(BehaviorTreeError):
        pass

    def raise_custom(_s: BaseState) -> PatternStatus:
        raise CustomBehaviorTreeError("expected")

    node = _action("custom", raise_custom)
    with pytest.raises(CustomBehaviorTreeError, match="expected"):
        node.tick(test_state)


# --- InteractiveLeaf ---


def test_interactive_leaf_deletes_input_after_handling(test_state: TestState) -> None:
    leaf = StubInteractiveLeaf("ask")
    test_state.set(leaf.input_key(), "answer")

    assert leaf.tick(test_state) == PatternStatus.SUCCESS
    assert not test_state.has(leaf.input_key())


def test_interactive_leaf_inside_sequence_resumes_after_input(test_state: TestState) -> None:
    executed: list[str] = []
    leaf = StubInteractiveLeaf("ask")
    node = SequenceNode(
        "seq",
        children=[
            _action("before", lambda _s: executed.append("before") or PatternStatus.SUCCESS),
            leaf,
            _action("after", lambda _s: executed.append("after") or PatternStatus.SUCCESS),
        ],
    )

    assert node.tick(test_state) == PatternStatus.WAITING_FOR_INPUT
    assert executed == ["before"]

    test_state.set(leaf.input_key(), "go")
    assert node.tick(test_state) == PatternStatus.SUCCESS
    assert executed == ["before", "after"]


# --- RootNode ---


def test_root_node_delegates_tick_to_child(test_state: TestState) -> None:
    marker = {"done": False}
    root = RootNode(
        "root",
        child=_action("work", lambda s: marker.update({"done": True}) or PatternStatus.SUCCESS),
    )
    assert root.tick(test_state) == PatternStatus.SUCCESS
    assert marker["done"] is True


def test_root_node_reset_propagates_to_subtree(test_state: TestState) -> None:
    counter = {"n": 0}

    def once(_s: BaseState) -> PatternStatus:
        counter["n"] += 1
        return PatternStatus.SUCCESS if counter["n"] == 1 else PatternStatus.FAILURE

    seq = SequenceNode("seq", children=[_action("once", once)])
    root = RootNode("root", child=seq)

    assert root.tick(test_state) == PatternStatus.SUCCESS
    assert root.tick(test_state) == PatternStatus.FAILURE

    root.reset()
    counter["n"] = 0
    assert root.tick(test_state) == PatternStatus.SUCCESS


def test_root_node_setup_runs_once_per_reset(test_state: TestState) -> None:
    setups: list[str] = []

    class SetupTrackingNode(LeafNode):
        def _setup(self, state: BaseState) -> None:
            setups.append(self.name)

        def _tick_impl(self, state: BaseState) -> PatternStatus:
            return PatternStatus.SUCCESS

    child = SetupTrackingNode("tracked")
    root = RootNode("root", child=child)

    root.tick(test_state)
    root.tick(test_state)
    assert setups == ["tracked"]

    root.reset()
    root.tick(test_state)
    assert setups == ["tracked", "tracked"]
