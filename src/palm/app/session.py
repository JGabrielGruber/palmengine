"""
CLI session bootstrap — thin PalmApp client for terminal entrypoints.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from palm.app.app import PalmApp
from palm.app.bootstrap import runtime_start_options
from palm.app.cli_settings import resolve_cli_settings
from palm.app.settings import PalmSettings
from palm.core.storage import StorageEngine


def create_console() -> Any:
    """Build a Rich console for CLI output."""
    try:
        from rich.console import Console

        return Console(highlight=False)
    except ImportError as exc:
        raise SystemExit(
            "Rich is required for the Palm CLI. Install with: pip install palmengine[cli]"
        ) from exc


def create_cli_app(
    *,
    storage_backend: str | None = None,
    data_dir: Path | None = None,
    storage: StorageEngine | None = None,
    settings: PalmSettings | None = None,
) -> PalmApp:
    """
    Construct a fully bootstrapped :class:`~palm.app.app.PalmApp` for the CLI.

    Settings resolve from ``PALM_*`` environment variables, with optional CLI flag
    overrides. ``bootstrap_cli`` wires the embedded runtime, ``InstanceManager``,
    persistence hooks, and definition catalog — no manual runtime assembly.

    Shared ``storage`` enables resume across separate CLI invocations (daemon +
    terminal) when both use the same engine instance or durable backend + data dir.
    """
    if settings is not None:
        cfg = settings
        if storage_backend is not None:
            cfg = resolve_cli_settings(storage_backend=storage_backend, settings=cfg)
        if data_dir is not None:
            cfg = resolve_cli_settings(data_dir=data_dir, settings=cfg)
    else:
        shared_backend = (
            storage.backend_name
            if storage is not None and storage.is_initialized and storage.backend_name
            else None
        )
        cfg = resolve_cli_settings(
            storage_backend=storage_backend,
            data_dir=data_dir,
            align_shared_storage=shared_backend if storage_backend is None else None,
        )

    app = PalmApp(cfg, storage=storage)
    app.bootstrap()
    app.bootstrap_cli(**runtime_start_options(cfg))
    return app