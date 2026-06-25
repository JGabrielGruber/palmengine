"""Built-in CQRS projections."""

from palm.common.cqrs.projections.instance_index import (
    InstanceIndexProjection,
    InstanceReadModel,
)
from palm.common.cqrs.projections.job_status_board import (
    JobStatusBoardProjection,
    JobStatusReadModel,
)
from palm.common.cqrs.projections.resource_invocation import (
    ResourceInvocationProjection,
    ResourceInvocationReadModel,
)

__all__ = [
    "InstanceIndexProjection",
    "InstanceReadModel",
    "JobStatusBoardProjection",
    "JobStatusReadModel",
    "ResourceInvocationProjection",
    "ResourceInvocationReadModel",
]
