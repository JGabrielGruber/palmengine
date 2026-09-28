"""
StorageFactory — settings-driven backend options.

The storage module map lives in ``drivers.storages.load``. This class does
not import a driver.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

_DEFAULT_DATA_DIR = Path("data")


class StorageFactory:
    """Build constructor options for a storage backend the bundle will open."""

    @staticmethod
    def resolve_data_dir(data_dir: Path | None) -> Path:
        """Return the effective data directory for filesystem persistence."""
        return data_dir if data_dir is not None else _DEFAULT_DATA_DIR

    @staticmethod
    def backend_options(
        *,
        storage_backend: str = "memory",
        data_dir: Path | None = None,
        **overrides: Any,
    ) -> dict[str, Any]:
        """
        Build keyword arguments forwarded to the backend constructor.

        Accepts either a :class:`~palm.app.settings.PalmSettings` instance via
        ``settings=`` or explicit ``storage_backend`` / ``data_dir`` fields.
        """
        settings = overrides.pop("settings", None)
        if settings is not None:
            storage_backend = str(getattr(settings, "storage_backend", storage_backend))
            data_dir = getattr(settings, "data_dir", data_dir)

        backend = storage_backend.strip().lower()
        options: dict[str, Any] = dict(overrides)
        if backend == "filesystem":
            options.setdefault("data_dir", StorageFactory.resolve_data_dir(data_dir))
        return options


__all__ = ["StorageFactory"]
