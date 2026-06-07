"""Smoke tests for palm.common package layout and backward-compat shims."""

from __future__ import annotations


def test_common_public_api() -> None:
    from palm.common import (
        DefinitionExecutor,
        ExecutionPlan,
        InstancePersistenceHook,
        PlanRegistry,
        ProcessPlan,
        build_pattern,
    )

    assert DefinitionExecutor is not None
    assert ExecutionPlan is not None
    assert ProcessPlan is not None
    assert PlanRegistry is not None
    assert InstancePersistenceHook is not None
    assert callable(build_pattern)


def test_executions_compat_reexports_common() -> None:
    import palm.common as common
    import palm.executions as executions

    assert executions.DefinitionExecutor is common.DefinitionExecutor
    assert executions.ExecutionPlan is common.ExecutionPlan
    assert executions.InstancePersistenceHook is common.InstancePersistenceHook


def test_common_subpackage_imports() -> None:
    from palm.common.hooks import InstancePersistenceHook
    from palm.common.patterns import PatternBuildContext, build_pattern
    from palm.common.persistence import DefinitionRepository, InstanceRepository
    from palm.common.plans import ExecutionPlan, PlanRegistry, ProcessPlan

    assert InstancePersistenceHook.__name__ == "InstancePersistenceHook"
    assert DefinitionRepository.__name__ == "DefinitionRepository"
    assert InstanceRepository.__name__ == "InstanceRepository"
    assert PatternBuildContext.__name__ == "PatternBuildContext"
    assert ExecutionPlan.__name__ == "ExecutionPlan"
    assert ProcessPlan.__name__ == "ProcessPlan"
    assert PlanRegistry.__name__ == "PlanRegistry"
    assert callable(build_pattern)