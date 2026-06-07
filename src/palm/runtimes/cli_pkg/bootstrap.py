"""
CLI startup — thin session opener delegating to :mod:`palm.app.session`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from palm.app.session import create_cli_app, create_console
from palm.app.settings import PalmSettings
from palm.core.storage import StorageEngine
from palm.runtimes.cli_pkg.context import CliContext


def bootstrap_runtime(
    *,
    storage_backend: str = "memory",
    data_dir: Path | None = None,
    storage: StorageEngine | None = None,
    settings: PalmSettings | None = None,
) -> CliContext:
    """Open a CLI session backed by a bootstrapped :class:`~palm.app.app.PalmApp`."""
    app = create_cli_app(
        storage_backend=storage_backend,
        data_dir=data_dir,
        storage=storage,
        settings=settings,
    )
    return CliContext(app=app, console=create_console())


def shutdown_context(ctx: CliContext) -> None:
    ctx.app.shutdown()