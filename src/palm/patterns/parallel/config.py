"""
Parallel pattern configuration — branches, merge strategy, and sub-flow refs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from palm.core.behavior_tree import ParallelPolicy

MergeStrategy = Literal["all", "any", "first"]


@dataclass(frozen=True)
class BranchConfig:
    """One parallel branch — inline pattern or reference to another flow."""

    slug: str
    flow_ref: str | None = None
    pattern: str | None = None
    options: dict[str, Any] | None = None
    state_schema: dict[str, Any] | None = None
    state_schema_ref: str | None = None
    result_key: str | None = None

    def __post_init__(self) -> None:
        if not self.slug:
            raise ValueError("Branch slug must be non-empty")
        if not self.flow_ref and not self.pattern:
            raise ValueError(
                f"Branch {self.slug!r} requires flow_ref or inline pattern/options",
            )

    @property
    def output_key(self) -> str:
        return self.result_key if self.result_key else self.slug

    @property
    def has_state_schema(self) -> bool:
        return self.state_schema is not None or self.state_schema_ref is not None


@dataclass(frozen=True)
class ParallelConfig:
    """Full parallel flow definition."""

    branches: tuple[BranchConfig, ...]
    merge_strategy: MergeStrategy = "all"
    merge_result_key: str = "merged"

    def __post_init__(self) -> None:
        if not self.branches:
            raise ValueError("ParallelConfig requires at least one branch")
        slugs = [branch.slug for branch in self.branches]
        if len(slugs) != len(set(slugs)):
            raise ValueError("Parallel branch slugs must be unique")

    @property
    def parallel_policy(self) -> ParallelPolicy:
        if self.merge_strategy in ("any", "first"):
            return ParallelPolicy.SUCCESS_ON_ANY
        return ParallelPolicy.SUCCESS_ON_ALL