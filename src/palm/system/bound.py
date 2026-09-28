"""Bound drivers the bundle passes into system start (0.72.6).

This module imports nothing from ``drivers``, ``plugins``, ``bundles``,
``services``, or a loader.
"""

from __future__ import annotations

from dataclasses import dataclass

from palm.core.storage.base_backend import BaseBackend

BOUND_DRIVERS_VERSION = 1


@dataclass(frozen=True)
class WorkloadRuntimeSlot:
    """Runtime names the bundle registered, plus the default name."""

    names: tuple[str, ...]
    default: str

    def __post_init__(self) -> None:
        if not self.names:
            raise ValueError("workload runtime slot has no names")
        if self.default not in self.names:
            raise ValueError(
                f"workload runtime default {self.default!r} is not in {list(self.names)}"
            )


@dataclass(frozen=True)
class BoundDrivers:
    """Storage the bundle opened, and the optional workload-runtime slot.

    ``version`` is the contract ``start`` accepts. An empty workload slot is
    ``workload_runtime is None``.
    """

    version: int
    storage: BaseBackend
    workload_runtime: WorkloadRuntimeSlot | None = None


__all__ = ["BOUND_DRIVERS_VERSION", "BoundDrivers", "WorkloadRuntimeSlot"]
