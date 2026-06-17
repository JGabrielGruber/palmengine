"""
Projection rebuild policy — batching and safeguards for large instance counts.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ProjectionRebuildPolicy:
    """Controls projection rebuild behaviour on host startup."""

    batch_size: int = 100
    max_instances: int = 5000
    skip_if_fresh: bool = True
    force: bool = False


@dataclass
class ProjectionRebuildReport:
    """Outcome of a coordinated projection rebuild."""

    counts: dict[str, int] = field(default_factory=dict)
    skipped: list[str] = field(default_factory=list)
    batched: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "counts": dict(self.counts),
            "skipped": list(self.skipped),
            "batched": list(self.batched),
            "warnings": list(self.warnings),
        }
