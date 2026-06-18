"""REST resource handlers."""

from palm.runtimes.server.surfaces.rest.handlers import (
    catalog,
    instances,
    jobs,
    meta,
    plans,
    snapshots,
    wizard,
)

__all__ = ["catalog", "instances", "jobs", "meta", "plans", "snapshots", "wizard"]
