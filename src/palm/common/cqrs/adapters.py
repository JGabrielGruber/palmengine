"""
CQRS adapters — bridge read models to existing Palm types.
"""

from __future__ import annotations

from palm.common.cqrs.projections.instance_index import InstanceReadModel
from palm.common.managers import InstanceSummary


def read_model_to_summary(model: InstanceReadModel) -> InstanceSummary:
    """Convert a projection row into an :class:`~palm.common.managers.InstanceSummary`."""
    return InstanceSummary(
        instance_id=model.instance_id,
        job_id=model.job_id,
        status=model.status,
        flow_name=model.flow_name,
        process_name=model.process_name,
        wizard_step_slug=model.wizard_step_slug,
        updated_at=model.updated_at,
        snapshot_count=model.snapshot_count,
    )
