"""
CLI settings resolution — env-first, flag overrides only when explicit.
"""

from __future__ import annotations

from pathlib import Path

from palm.app.settings import PalmSettings, SchedulerPolicy
from palm.common.storage import StorageFactory

DURABLE_STORAGE_BACKENDS: frozenset[str] = frozenset({"filesystem", "postgres", "mongodb"})


def is_durable_storage(backend: str | None) -> bool:
    """Return whether ``backend`` persists data across process restarts."""
    if not backend:
        return False
    return backend.strip().lower() in DURABLE_STORAGE_BACKENDS


def resolve_cli_settings(
    *,
    storage_backend: str | None = None,
    data_dir: Path | None = None,
    settings: PalmSettings | None = None,
    align_shared_storage: str | None = None,
    enable_state_snapshot: bool | None = None,
    max_loaded_instances: int | None = None,
    max_concurrent_active: int | None = None,
    default_scheduler: SchedulerPolicy | None = None,
) -> PalmSettings:
    """
    Build CLI settings with environment variables as the base.

    Precedence (highest last):

    1. ``PALM_*`` environment variables via :class:`~palm.app.settings.PalmSettings`
    2. ``--config`` file (loaded into ``PalmSettings`` before this merge)
    3. Explicit ``settings`` argument (when passed to bootstrap)
    4. CLI flags (only when not ``None``)
    5. ``align_shared_storage`` — backend name from a pre-opened shared engine
    """
    cfg = settings.model_copy(deep=True) if settings is not None else PalmSettings()

    if storage_backend is not None:
        cfg.storage_backend = storage_backend
    if data_dir is not None:
        cfg.data_dir = data_dir
    if align_shared_storage is not None:
        cfg.storage_backend = align_shared_storage
    if enable_state_snapshot is not None:
        cfg.enable_state_snapshot = enable_state_snapshot
    if max_loaded_instances is not None:
        cfg.max_loaded_instances = max_loaded_instances
    if max_concurrent_active is not None:
        cfg.max_concurrent_active = max_concurrent_active
    if default_scheduler is not None:
        cfg.default_scheduler = default_scheduler

    if is_durable_storage(cfg.storage_backend) and cfg.data_dir is None:
        cfg.data_dir = StorageFactory.resolve_data_dir(None)
    return cfg