"""REST resource handlers (legacy monolith routes)."""

from palm.runtimes.server.surfaces.rest.handlers import (
    instances,
    jobs,
    meta,
    plans,
    snapshots,
)

__all__ = [
    "instances",
    "jobs",
    "meta",
    "plans",
    "snapshots",
]