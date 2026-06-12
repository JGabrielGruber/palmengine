"""
Merge strategies for parallel branch results.
"""

from __future__ import annotations

from typing import Any

from palm.core.context import BaseState
from palm.core.exceptions import StateValidationError
from palm.patterns.parallel.config import BranchConfig, MergeStrategy, ParallelConfig
from palm.patterns.parallel.keys import ParallelKeys


def get_branch_results(state: BaseState) -> dict[str, Any]:
    raw = state.get(ParallelKeys.BRANCH_RESULTS)
    return dict(raw) if isinstance(raw, dict) else {}


def record_branch_result(
    state: BaseState,
    branch: BranchConfig,
    result: dict[str, Any],
) -> None:
    """Store a completed branch payload on the parent state."""
    results = get_branch_results(state)
    results[branch.slug] = result
    state.set(ParallelKeys.BRANCH_RESULTS, results)


def merge_branch_results(state: BaseState, config: ParallelConfig) -> dict[str, Any]:
    """Apply the configured merge strategy and validate against the parent schema."""
    results = get_branch_results(state)
    merged = _apply_merge_strategy(config.branches, results, config.merge_strategy)
    _validate_merged(state, merged, config)
    state.set(ParallelKeys.MERGED, merged)
    state.set(ParallelKeys.MERGE_COMPLETE, True)
    if config.merge_result_key:
        state.set(config.merge_result_key, merged)
    return merged


def _apply_merge_strategy(
    branches: tuple[BranchConfig, ...],
    results: dict[str, Any],
    strategy: MergeStrategy,
) -> dict[str, Any]:
    if strategy == "all":
        return _merge_all(branches, results)
    if strategy == "any":
        return _merge_any(branches, results)
    if strategy == "first":
        return _merge_first(branches, results)
    raise ValueError(f"Unknown merge strategy: {strategy!r}")


def _merge_all(branches: tuple[BranchConfig, ...], results: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for branch in branches:
        payload = results.get(branch.slug)
        if not isinstance(payload, dict) or payload.get("status") != "success":
            raise StateValidationError(f"Branch {branch.slug!r} did not complete successfully")
        merged[branch.output_key] = _branch_value(payload)
    return merged


def _merge_any(branches: tuple[BranchConfig, ...], results: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for branch in branches:
        payload = results.get(branch.slug)
        if isinstance(payload, dict) and payload.get("status") == "success":
            merged[branch.output_key] = _branch_value(payload)
    if not merged:
        raise StateValidationError("No parallel branch completed successfully")
    return merged


def _merge_first(branches: tuple[BranchConfig, ...], results: dict[str, Any]) -> dict[str, Any]:
    for branch in branches:
        payload = results.get(branch.slug)
        if isinstance(payload, dict) and payload.get("status") == "success":
            return {branch.output_key: _branch_value(payload)}
    raise StateValidationError("No parallel branch completed successfully")


def _branch_value(payload: dict[str, Any]) -> Any:
    if "answers" in payload:
        return payload["answers"]
    if "value" in payload:
        return payload["value"]
    return payload


def _validate_merged(state: BaseState, merged: dict[str, Any], config: ParallelConfig) -> None:
    schema = state.schema
    if schema is None:
        return
    if config.merge_strategy == "all":
        errors = schema.validate_state(merged)
    else:
        errors = []
        for key, value in merged.items():
            try:
                schema.validate_key(key, value)
            except StateValidationError as exc:
                errors.append(str(exc))
    if errors:
        raise StateValidationError(errors[0])