"""Migration metadata keys shared by instance sync and migration execution."""

from __future__ import annotations

from typing import Any

MIGRATION_METADATA_KEYS = frozenset(
    {
        "migration_status",
        "migration_target_revision",
        "migration_from_revision",
        "migration_blockers",
    }
)


def preserve_migration_metadata(
    instance_metadata: dict[str, Any],
    job_metadata: dict[str, Any],
) -> dict[str, Any]:
    """Merge job metadata while retaining instance-owned migration fields."""
    merged = dict(job_metadata)
    for key in MIGRATION_METADATA_KEYS:
        if key in instance_metadata:
            merged[key] = instance_metadata[key]
    return merged


__all__ = ["MIGRATION_METADATA_KEYS", "preserve_migration_metadata"]