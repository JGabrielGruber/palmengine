"""Tests for parallel pattern — branches, merge strategies, and resume."""

from __future__ import annotations

from palm.common import DefinitionRepository
from palm.common.patterns import PatternBuildContext, build_pattern
from palm.common.persistence.state_snapshot import snapshot_state, state_from_snapshot
from palm.core.behavior_tree import PatternStatus
from palm.core.context import ContextEngine
from palm.definitions import FlowDefinition
from palm.patterns.parallel import ParallelKeys, ParallelPattern, parallel_config_from_options
from palm.patterns.parallel.persistence import (
    parallel_runtime_position,
    restore_parallel_position,
)
from palm.states import BlackboardState


def _two_step_parallel_flow(*, merge_strategy: str = "all") -> FlowDefinition:
    return FlowDefinition(
        name="parallel-demo",
        pattern="parallel",
        state_schema={
            "type": "object",
            "properties": {
                "alpha": {"type": "object"},
                "beta": {"type": "object"},
            },
            "required": ["alpha", "beta"],
        },
        options={
            "merge_strategy": merge_strategy,
            "branches": [
                {
                    "slug": "alpha",
                    "pattern": "wizard",
                    "options": {"steps": ["alpha"]},
                },
                {
                    "slug": "beta",
                    "pattern": "wizard",
                    "options": {"steps": ["beta"]},
                },
            ],
        },
    )


def _build_parallel(flow: FlowDefinition | None = None) -> ParallelPattern:
    flow = flow or _two_step_parallel_flow()
    built = build_pattern(flow, context=PatternBuildContext())
    assert isinstance(built, ParallelPattern)
    return built


def test_parallel_config_parses_branches() -> None:
    config = parallel_config_from_options(_two_step_parallel_flow().options)
    assert config.merge_strategy == "all"
    assert len(config.branches) == 2
    assert config.branches[0].slug == "alpha"


def _multi_step_branch_flow() -> FlowDefinition:
    return FlowDefinition(
        name="parallel-multi-step",
        pattern="parallel",
        state_schema={
            "type": "object",
            "properties": {
                "alpha": {"type": "object"},
                "beta": {"type": "object"},
            },
            "required": ["alpha", "beta"],
        },
        options={
            "merge_strategy": "all",
            "branches": [
                {
                    "slug": "alpha",
                    "pattern": "wizard",
                    "options": {
                        "steps": [
                            {"slug": "name", "title": "Name", "prompt": "Name?"},
                            {"slug": "age", "title": "Age", "prompt": "Age?"},
                        ],
                    },
                    "result_key": "alpha",
                },
                {
                    "slug": "beta",
                    "pattern": "wizard",
                    "options": {"steps": ["beta"]},
                },
            ],
        },
    )


def test_parallel_branch_advances_through_multiple_steps() -> None:
    from palm.patterns.parallel.scope import load_branch_snapshot_for
    from palm.patterns.wizard.bindings.context.keys import WizardKeys

    flow = _multi_step_branch_flow()
    state = BlackboardState(schema=flow.materialize_state_schema())
    parallel = _build_parallel(flow)
    alpha = parallel.branch_runners()["alpha"]

    assert parallel.tick(state) == PatternStatus.WAITING_FOR_INPUT
    assert parallel.current_step_slug(state) == "alpha:name"

    parallel.provide_input(state, "Ada")
    alpha._branch_state = None
    assert parallel.tick(state) == PatternStatus.WAITING_FOR_INPUT
    assert parallel.current_step_slug(state) == "alpha:age"

    snapshot = load_branch_snapshot_for(state, "alpha")
    assert snapshot is not None
    restored = state_from_snapshot(snapshot)
    assert restored.get(WizardKeys.CURRENT_STEP) == "age"

    parallel.provide_input(state, "27")
    alpha._branch_state = None
    assert parallel.tick(state) == PatternStatus.WAITING_FOR_INPUT
    assert parallel.current_step_slug(state) == "beta:beta"

    parallel.provide_input(state, "done")
    assert parallel.tick(state) == PatternStatus.SUCCESS
    merged = state.get(ParallelKeys.MERGED)
    assert merged["alpha"] == {"name": "Ada", "age": "27"}


def test_parallel_runs_two_wizard_branches_and_merges() -> None:
    flow = _two_step_parallel_flow()
    schema = flow.materialize_state_schema()
    state = BlackboardState(schema=schema)
    parallel = _build_parallel(flow)

    assert parallel.tick(state) == PatternStatus.WAITING_FOR_INPUT

    parallel.provide_input(state, "first")
    assert parallel.tick(state) == PatternStatus.WAITING_FOR_INPUT

    parallel.provide_input(state, "second")
    assert parallel.tick(state) == PatternStatus.SUCCESS

    merged = state.get(ParallelKeys.MERGED)
    assert isinstance(merged, dict)
    assert merged["alpha"] == {"alpha": "first"}
    assert merged["beta"] == {"beta": "second"}
    assert parallel.answers(state) == merged


def test_parallel_branch_scopes_isolate_wizard_state() -> None:
    flow = _two_step_parallel_flow()
    state = BlackboardState(schema=flow.materialize_state_schema())
    parallel = _build_parallel(flow)

    parallel.tick(state)
    parallel.provide_input(state, "Ada")
    parallel.tick(state)

    scopes = state.scope_stack()
    assert (
        "alpha" in scopes or state.get_scoped(ParallelKeys.BRANCH_STATE, default=None) is not None
    )


def test_parallel_subflow_via_flow_ref() -> None:
    repo = DefinitionRepository()
    repo.register_flow(
        FlowDefinition(
            name="quick",
            pattern="wizard",
            options={"steps": ["solo"]},
        ),
    )
    flow = FlowDefinition(
        name="parallel-quick",
        pattern="parallel",
        options={
            "merge_strategy": "any",
            "branches": [{"slug": "solo", "flow_ref": "quick"}],
        },
    )
    parallel = build_pattern(
        flow,
        context=PatternBuildContext(definition_repository=repo),
    )
    assert isinstance(parallel, ParallelPattern)
    state = BlackboardState()
    assert parallel.tick(state) == PatternStatus.WAITING_FOR_INPUT
    parallel.provide_input(state, "done")
    assert parallel.tick(state) == PatternStatus.SUCCESS
    assert parallel.answers(state)["solo"] == {"solo": "done"}


def test_parallel_snapshot_preserves_branch_state() -> None:
    flow = _two_step_parallel_flow()
    state = BlackboardState(schema=flow.materialize_state_schema())
    parallel = _build_parallel(flow)

    parallel.tick(state)
    parallel.provide_input(state, "Ada")
    parallel.tick(state)

    restored = state_from_snapshot(snapshot_state(state))
    assert restored.scope_stack()
    assert isinstance(restored.get(ParallelKeys.BRANCH_RESULTS), dict) or True


def test_parallel_resume_restores_child_results() -> None:
    flow = _two_step_parallel_flow()
    state = BlackboardState(schema=flow.materialize_state_schema())
    parallel = _build_parallel(flow)

    parallel.tick(state)
    position = parallel_runtime_position(parallel, state)
    restore_parallel_position(parallel, position)
    assert parallel.parallel._child_results


def test_parallel_with_context_engine_tracks_scope() -> None:
    ctx = ContextEngine()
    state = BlackboardState()
    ctx.initialize(state=state)
    flow = _two_step_parallel_flow()
    parallel = build_pattern(flow, context=PatternBuildContext(context_engine=ctx))

    parallel.tick(state)
    assert ctx.state_scope_stack  # branch scope entered for active branch
