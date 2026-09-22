"""Workload execution REST surface."""

from bundles.standard.runtimes.server.surfaces.rest.execution.workloads.routes import (
    register_workload_routes,
)

__all__ = ["register_workload_routes"]
