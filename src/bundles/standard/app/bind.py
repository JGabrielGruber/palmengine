"""Bind the drivers a standard-bundle start passes to the kernel."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from drivers.storages.load import open_backend

from palm.common.storage import StorageFactory
from palm.core.storage import StorageEngine
from palm.core.workload.registry import workload_runtime_registry
from palm.system.bound import BOUND_DRIVERS_VERSION, BoundDrivers, WorkloadRuntimeSlot

# The bundle binds memory when a runtime start did not name a backend.
_UNNAMED_STORAGE = "memory"


def workload_slot(
    *,
    names: tuple[str, ...] | None,
    default: str | None,
) -> WorkloadRuntimeSlot | None:
    """Build the workload slot from names the bundle already registered.

    ``names is None`` uses the registry as it stands. An empty name list is
    an empty slot.
    """
    registered = workload_runtime_registry.names()
    if names is None:
        chosen = tuple(registered)
    else:
        missing = [name for name in names if name not in registered]
        if missing:
            listed = ", ".join(missing)
            raise RuntimeError(f"workload runtime not registered: {listed}")
        chosen = tuple(names)
    if not chosen:
        return None
    picked = default if default is not None else ("local" if "local" in chosen else chosen[0])
    if picked not in chosen:
        raise RuntimeError(f"workload runtime default {picked!r} is not in {list(chosen)}")
    return WorkloadRuntimeSlot(names=chosen, default=picked)


def bind_storage(
    *,
    name: str,
    engine: StorageEngine | None = None,
    options: Mapping[str, Any] | None = None,
    workload_names: tuple[str, ...] | None = None,
    workload_default: str | None = None,
    allowed_storages: tuple[str, ...] | None = None,
    existing: BoundDrivers | None = None,
) -> BoundDrivers:
    """Open the named storage, or reuse one this process already attached."""
    normalized = name.strip().lower()
    if allowed_storages is not None and normalized not in allowed_storages:
        listed = ", ".join(allowed_storages)
        raise RuntimeError(f"storage {normalized!r} is not a storage the profile names ({listed})")
    storage: Any
    if (
        engine is not None
        and engine.is_initialized
        and engine.backend is not None
        and engine.backend.is_open
    ):
        if engine.backend_name != normalized:
            raise RuntimeError(
                f"storage is already {engine.backend_name!r}; the start names {normalized!r}"
            )
        storage = engine.backend
    elif existing is not None and existing.storage.is_open and existing.storage.name == normalized:
        storage = existing.storage
    else:
        storage = open_backend(normalized, **dict(options or {}))
    return BoundDrivers(
        version=BOUND_DRIVERS_VERSION,
        storage=storage,
        workload_runtime=workload_slot(names=workload_names, default=workload_default),
    )


def bind_from_settings(
    settings: Any,
    *,
    composition: Any = None,
    engine: StorageEngine | None = None,
    storage_backend: str | None = None,
    backend_options: Mapping[str, Any] | None = None,
    workload_default: str | None = None,
    existing: BoundDrivers | None = None,
) -> BoundDrivers:
    """Bind the storage ``settings`` names, checked against the profile."""
    name = str(storage_backend if storage_backend is not None else settings.storage_backend)
    allowed = tuple(composition.storages) if composition is not None else None
    runners = tuple(composition.runners) if composition is not None else None
    default = (
        workload_default
        if workload_default is not None
        else getattr(settings, "workload_default_runtime", None)
    )
    if storage_backend is None and not backend_options:
        options = StorageFactory.backend_options(settings=settings)
    else:
        options = StorageFactory.backend_options(
            storage_backend=name.strip().lower(),
            data_dir=getattr(settings, "data_dir", None),
            **dict(backend_options or {}),
        )
    picked = default if isinstance(default, str) else None
    return bind_storage(
        name=name,
        engine=engine,
        options=options,
        workload_names=runners,
        workload_default=picked,
        allowed_storages=allowed,
        existing=existing,
    )


def prepare_bound_start(
    engine: StorageEngine,
    options: Mapping[str, Any],
) -> dict[str, Any]:
    """Return start options whose storage and workload default are bound drivers.

    When ``drivers`` is already set, those slots are not read from the loose
    option names. Otherwise this bundle binds ``_UNNAMED_STORAGE`` when the
    caller did not name a backend.
    """
    prepared = dict(options)
    named = prepared.pop("storage_backend", None)
    backend_options = prepared.pop("backend_options", None)
    workload_default = prepared.pop("workload_default_runtime", None)
    if "drivers" in prepared:
        return prepared
    extra = backend_options if isinstance(backend_options, Mapping) else None
    default = workload_default if isinstance(workload_default, str) else None
    prepared["drivers"] = bind_storage(
        name=str(named) if named is not None else _UNNAMED_STORAGE,
        engine=engine,
        options=StorageFactory.backend_options(
            storage_backend=str(named) if named is not None else _UNNAMED_STORAGE,
            data_dir=prepared.get("data_dir"),
            **dict(extra or {}),
        ),
        workload_names=None,
        workload_default=default,
    )
    return prepared


__all__ = [
    "bind_from_settings",
    "bind_storage",
    "prepare_bound_start",
    "workload_slot",
]
