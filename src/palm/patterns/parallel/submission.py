"""
Parallel flow submission metadata.
"""

from __future__ import annotations

from typing import Any

from palm.definitions.flow import FlowDefinition
from palm.patterns.parallel.builder import parallel_config_from_options


def parallel_submission_metadata(flow: FlowDefinition) -> dict[str, Any]:
    """Enrich job metadata with parallel branch configuration."""
    try:
        config = parallel_config_from_options(flow.options or {})
    except Exception:
        return {}
    return {
        "parallel": {
            "merge_strategy": config.merge_strategy,
            "branch_slugs": [branch.slug for branch in config.branches],
        },
    }