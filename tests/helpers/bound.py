"""Bind drivers for a direct ``BaseRuntime.start`` in tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from bundles.standard.app.bind import bind_storage

from palm.common.storage import StorageFactory
from palm.system.bound import BoundDrivers


def bound_for_runtime(
    *,
    storage_backend: str = "memory",
    backend_options: dict[str, Any] | None = None,
    workload_default_runtime: str | None = None,
    data_dir: Path | str | None = None,
) -> BoundDrivers:
    """Open ``storage_backend`` and the workload runtimes already registered."""
    extra = dict(backend_options or {})
    directory = data_dir if data_dir is not None else extra.pop("data_dir", None)
    return bind_storage(
        name=storage_backend,
        options=StorageFactory.backend_options(
            storage_backend=storage_backend,
            data_dir=directory,
            **extra,
        ),
        workload_names=None,
        workload_default=workload_default_runtime,
    )


__all__ = ["bound_for_runtime"]
