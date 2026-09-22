"""DAG pattern v0 — resource nodes with deps (0.54.3)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from palm.core.behavior_tree import PatternStatus
from palm.core.resource.result import ProviderResult
from plugins.patterns.dag.bindings.definitions.config import (
    DagConfig,
    DagNodeSpec,
    topological_sort,
)
from plugins.patterns.dag.pattern import DagPattern
from palm.states.dict_backed_state import DictBackedState


def test_topo_sort_linear() -> None:
    nodes = (
        DagNodeSpec(id="a", resource_ref="r-a"),
        DagNodeSpec(id="b", resource_ref="r-b", depends_on=("a",)),
        DagNodeSpec(id="c", resource_ref="r-c", depends_on=("b",)),
    )
    ordered = topological_sort(nodes)
    assert [n.id for n in ordered] == ["a", "b", "c"]


def test_topo_sort_cycle_raises() -> None:
    nodes = (
        DagNodeSpec(id="a", resource_ref="r-a", depends_on=("b",)),
        DagNodeSpec(id="b", resource_ref="r-b", depends_on=("a",)),
    )
    with pytest.raises(ValueError, match="cycle"):
        topological_sort(nodes)


def test_implicit_chain_from_options() -> None:
    cfg = DagConfig.from_options(
        {
            "nodes": [
                {"id": "preflight", "resource_ref": "hermetic-preflight"},
                {"id": "job", "resource_ref": "hermetic-true-job"},
            ]
        }
    )
    assert cfg.nodes[0].depends_on == ()
    assert cfg.nodes[1].depends_on == ("preflight",)


def test_dag_runs_nodes_sequentially() -> None:
    engine = MagicMock()
    calls: list[str] = []

    def _invoke(ref, **kwargs):
        calls.append(str(ref))
        return ProviderResult.ok({"ref": ref, "n": len(calls)})

    engine.invoke.side_effect = _invoke
    engine.is_initialized = True

    cfg = DagConfig.from_options(
        {
            "nodes": [
                {"id": "a", "resource_ref": "res-a", "output_key": "out_a"},
                {"id": "b", "resource_ref": "res-b", "output_key": "out_b"},
            ]
        }
    )
    pattern = DagPattern(name="test-dag", config=cfg, resource_engine=engine)
    state = DictBackedState()

    # drain_ready default: whole linear chain in one tick
    assert pattern.tick(state) == PatternStatus.SUCCESS
    assert calls == ["res-a", "res-b"]
    assert state.get("out_a") == {"ref": "res-a", "n": 1}
    assert state.get("out_b") == {"ref": "res-b", "n": 2}
    assert state.get("dag")["status"] == "succeeded"


def test_dag_fails_on_resource_error() -> None:
    engine = MagicMock()
    engine.is_initialized = True
    engine.invoke.return_value = ProviderResult.fail("boom")

    cfg = DagConfig.from_options(
        {"nodes": [{"id": "only", "resource_ref": "x"}]}
    )
    pattern = DagPattern(config=cfg, resource_engine=engine)
    state = DictBackedState()
    assert pattern.tick(state) == PatternStatus.FAILURE
    assert state.get("dag")["status"] == "failed"


def test_fan_out_deps_run_after_preflight() -> None:
    """preflight → (a, b) → join; one ready node per tick (stable order)."""
    engine = MagicMock()
    calls: list[str] = []

    def _invoke(ref, **kwargs):
        # encode node via output tracking — invoke only gets resource_ref
        calls.append(str(ref))
        return ProviderResult.ok({"ok": True, "n": len(calls)})

    engine.invoke.side_effect = _invoke
    engine.is_initialized = True

    cfg = DagConfig.from_options(
        {
            "chain_implicit": False,
            "nodes": [
                {"id": "preflight", "resource_ref": "health-res"},
                {
                    "id": "branch_a",
                    "resource_ref": "job-res",
                    "depends_on": ["preflight"],
                    "output_key": "a",
                },
                {
                    "id": "branch_b",
                    "resource_ref": "job-res",
                    "depends_on": ["preflight"],
                    "output_key": "b",
                },
                {
                    "id": "join",
                    "resource_ref": "job-res",
                    "depends_on": ["branch_a", "branch_b"],
                    "output_key": "j",
                },
            ],
        }
    )
    pattern = DagPattern(config=cfg, resource_engine=engine)
    state = DictBackedState()

    # 0.54.8 drain_ready: whole fan-out completes in one tick
    assert pattern.tick(state) == PatternStatus.SUCCESS
    assert calls == ["health-res", "job-res", "job-res", "job-res"]
    assert state.get("a") is not None and state.get("b") is not None
    assert state.get("j") is not None
    assert state.get("dag")["status"] == "succeeded"


def test_drain_ready_false_one_node_per_tick() -> None:
    engine = MagicMock()
    calls: list[str] = []

    def _invoke(ref, **kwargs):
        calls.append(str(ref))
        return ProviderResult.ok({"n": len(calls)})

    engine.invoke.side_effect = _invoke
    engine.is_initialized = True
    cfg = DagConfig.from_options(
        {
            "drain_ready": False,
            "chain_implicit": False,
            "nodes": [
                {"id": "preflight", "resource_ref": "h"},
                {"id": "a", "resource_ref": "j", "depends_on": ["preflight"]},
                {"id": "b", "resource_ref": "j", "depends_on": ["preflight"]},
            ],
        }
    )
    pattern = DagPattern(config=cfg, resource_engine=engine)
    state = DictBackedState()
    assert pattern.tick(state) == PatternStatus.RUNNING
    assert calls == ["h"]
    assert pattern.tick(state) == PatternStatus.RUNNING
    assert calls == ["h", "j"]
    assert pattern.tick(state) == PatternStatus.SUCCESS
    assert calls == ["h", "j", "j"]


def test_builder_wires_resource_engine() -> None:
    from palm.common.patterns.build_context import PatternBuildContext
    from palm.definitions.flow import FlowDefinition
    from plugins.patterns.dag.bindings.definitions.builder import build
    from plugins.patterns.dag.pattern import DagPattern as DP

    flow = FlowDefinition(
        name="hermetic-dag",
        pattern="dag",
        options={
            "nodes": [
                {"id": "a", "resource_ref": "hermetic-preflight"},
                {"id": "b", "resource_ref": "hermetic-true-job"},
            ]
        },
    )
    engine = MagicMock()
    ctx = PatternBuildContext(resource_engine=engine)
    pattern = build(flow, ctx, DP)
    assert isinstance(pattern, DP)
    assert pattern.config.nodes[1].depends_on == ("a",)
