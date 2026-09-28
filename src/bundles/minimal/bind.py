"""Bind the minimal bundle's drivers before system start."""

from __future__ import annotations

from drivers.storages.load import open_backend

from palm.system.bound import BOUND_DRIVERS_VERSION, BoundDrivers


def bind_memory() -> BoundDrivers:
    """Open memory storage. The workload-runtime slot stays empty."""
    return BoundDrivers(
        version=BOUND_DRIVERS_VERSION,
        storage=open_backend("memory"),
        workload_runtime=None,
    )


__all__ = ["bind_memory"]
