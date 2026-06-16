"""Built-in CQRS projections."""

from palm.common.cqrs.projections.instance_index import (
    InstanceIndexProjection,
    InstanceReadModel,
)

__all__ = ["InstanceIndexProjection", "InstanceReadModel"]