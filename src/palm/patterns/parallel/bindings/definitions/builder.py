"""
Parallel pattern builder — parse flow options into ``ParallelPattern`` instances.
"""

from __future__ import annotations

from typing import Any

from palm.common.exceptions import DefinitionBuildError, DefinitionNotFoundError
from palm.common.patterns.build_context import PatternBuildContext
from palm.core.behavior_tree import BasePattern
from palm.definitions.flow import FlowDefinition
from palm.patterns.parallel.bindings.definitions.config import BranchConfig, ParallelConfig
from palm.patterns.parallel.flow.branch import BranchRunner
from palm.patterns.parallel.pattern import ParallelPattern


def build(
    flow: FlowDefinition,
    context: PatternBuildContext,
    pattern_cls: type[BasePattern],
) -> BasePattern:
    """Instantiate a parallel pattern from a flow definition."""
    if not issubclass(pattern_cls, ParallelPattern):
        raise DefinitionBuildError("Registry entry for 'parallel' is not ParallelPattern")

    config = parallel_config_from_options(flow.options or {})
    runners = [_build_branch_runner(branch, context, flow.name) for branch in config.branches]
    return pattern_cls(
        name=flow.name,
        config=config,
        runners=runners,
        event_engine=context.event_engine,
        context_engine=context.context_engine,
    )


def parallel_config_from_options(options: dict[str, Any]) -> ParallelConfig:
    raw_branches = options.get("branches")
    if not isinstance(raw_branches, list) or not raw_branches:
        raise DefinitionBuildError("Parallel flow requires a non-empty 'branches' list")

    merge_strategy = str(options.get("merge_strategy", "all"))
    if merge_strategy not in {"all", "any", "first"}:
        raise DefinitionBuildError(f"Invalid merge_strategy: {merge_strategy!r}")

    merge_result_key = options.get("merge_result_key", "merged")
    branches = tuple(_parse_branch(item) for item in raw_branches)
    return ParallelConfig(
        branches=branches,
        merge_strategy=merge_strategy,  # type: ignore[arg-type]
        merge_result_key=str(merge_result_key),
    )


def _parse_branch(data: Any) -> BranchConfig:
    if not isinstance(data, dict):
        raise DefinitionBuildError("Each parallel branch must be a mapping")
    slug = data.get("slug")
    if not slug:
        raise DefinitionBuildError("Parallel branch requires 'slug'")
    inline_schema = data.get("state_schema")
    state_schema = dict(inline_schema) if isinstance(inline_schema, dict) else None
    ref = data.get("state_schema_ref")
    state_schema_ref = str(ref) if ref else None
    options = data.get("options")
    branch_options = dict(options) if isinstance(options, dict) else None
    return BranchConfig(
        slug=str(slug),
        flow_ref=str(data["flow_ref"]) if data.get("flow_ref") else None,
        pattern=str(data["pattern"]) if data.get("pattern") else None,
        options=branch_options,
        state_schema=state_schema,
        state_schema_ref=state_schema_ref,
        result_key=str(data["result_key"]) if data.get("result_key") else None,
    )


def _build_branch_runner(
    branch: BranchConfig,
    context: PatternBuildContext,
    parent_name: str,
) -> BranchRunner:
    from palm.common.patterns.builder import build_pattern

    child_flow = _resolve_branch_flow(branch, context, parent_name)
    executable = build_pattern(child_flow, context=context)
    return BranchRunner(
        branch,
        executable,
        context_engine=context.context_engine,
        repository=context.definition_repository,
    )


def _resolve_branch_flow(
    branch: BranchConfig,
    context: PatternBuildContext,
    parent_name: str,
) -> FlowDefinition:
    if branch.flow_ref:
        repository = context.definition_repository
        if repository is None:
            raise DefinitionBuildError(
                f"Branch {branch.slug!r} uses flow_ref but no definition repository is available",
            )
        try:
            return repository.get_flow(branch.flow_ref)
        except DefinitionNotFoundError:
            try:
                return repository.get_flow(branch.flow_ref, by_id=True)
            except DefinitionNotFoundError as exc:
                raise DefinitionBuildError(
                    f"Branch {branch.slug!r} flow_ref {branch.flow_ref!r} not found",
                ) from exc

    if branch.pattern:
        return FlowDefinition(
            name=f"{parent_name}:{branch.slug}",
            pattern=branch.pattern,
            options=dict(branch.options or {}),
            state_schema=branch.state_schema,
            state_schema_ref=branch.state_schema_ref,
        )

    raise DefinitionBuildError(f"Branch {branch.slug!r} has no flow_ref or pattern")
