"""
CLI settings resolution — env-first, flag overrides only when explicit.
"""

from __future__ import annotations

from pathlib import Path

from palm.app.settings import PalmSettings
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
) -> PalmSettings:
    """
    Build CLI settings with environment variables as the base.

    Precedence (highest last):

    1. ``PALM_*`` environment variables via :class:`~palm.app.settings.PalmSettings`
    2. Explicit ``settings`` argument (when passed to bootstrap)
    3. CLI flags ``storage_backend`` / ``data_dir`` (only when not ``None``)
    4. ``align_shared_storage`` — backend name from a pre-opened shared engine
    """
    cfg = settings.model_copy(deep=True) if settings is not None else PalmSettings()

    if storage_backend is not None:
        cfg.storage_backend = storage_backend
    if data_dir is not None:
        cfg.data_dir = data_dir
    if align_shared_storage is not None:
        cfg.storage_backend = align_shared_storage

    if is_durable_storage(cfg.storage_backend) and cfg.data_dir is None:
        cfg.data_dir = StorageFactory.resolve_data_dir(None)
    return cfg