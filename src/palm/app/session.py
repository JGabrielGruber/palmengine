"""
CLI session bootstrap — ApplicationHost entry for terminal surfaces.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

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


def create_cli_host(
    *,
    storage_backend: str | None = None,
    data_dir: Path | None = None,
    storage: StorageEngine | None = None,
    settings: PalmSettings | None = None,
) -> Any:
    """
    Construct a started :class:`~palm.app.host.ApplicationHost` for the CLI.

    Uses the collapsed ``all_in_one`` profile so command/query buses and
    projections are available to terminal commands.
    """
    from palm.app.bootstrap import deployment_profile_from_settings
    from palm.app.host.application_host import ApplicationHost

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

    host = ApplicationHost(cfg, profile=deployment_profile_from_settings(cfg), storage=storage)
    host.start(**runtime_start_options(cfg))
    return host
