"""
CLI session bootstrap — authoritative PalmApp wiring for terminal clients.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from palm.app.app import PalmApp
from palm.app.settings import PalmSettings
from palm.core.storage import StorageEngine


def create_console() -> Any:
    """Build a Rich console for CLI output."""
    try:
        from rich.console import Console

        return Console(highlight=False)
    except ImportError as exc:
        raise SystemExit(
            "Rich is required for the Palm CLI. Install with: uv sync --extra cli"
        ) from exc


def create_cli_app(
    *,
    storage_backend: str = "memory",
    data_dir: Path | None = None,
    storage: StorageEngine | None = None,
    settings: PalmSettings | None = None,
) -> PalmApp:
    """
    Construct a bootstrapped :class:`~palm.app.app.PalmApp` with the CLI runtime.

    Shared ``storage`` enables resume across separate CLI invocations (daemon +
    terminal) when both use the same engine instance or backend.
    """
    cfg = settings or PalmSettings(storage_backend=storage_backend, data_dir=data_dir)
    if storage_backend and settings is None:
        cfg.storage_backend = storage_backend
    if data_dir is not None and settings is None:
        cfg.data_dir = data_dir

    app = PalmApp(cfg, storage=storage)
    app.bootstrap()
    if storage is None:
        app.bootstrap_cli(storage_backend=cfg.storage_backend)
    else:
        app.bootstrap_cli()
    return app