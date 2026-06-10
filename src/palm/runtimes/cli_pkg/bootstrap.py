"""
CLI startup — thin session opener delegating entirely to :mod:`palm.app.session`.
"""

from __future__ import annotations

from pathlib import Path

from palm.app.session import create_cli_app, create_console
from palm.app.settings import PalmSettings
from palm.core.storage import StorageEngine
from palm.runtimes.cli_pkg.context import CliContext
from palm.runtimes.cli_pkg.startup import print_startup_banner


def bootstrap_runtime(
    *,
    storage_backend: str | None = None,
    data_dir: Path | None = None,
    storage: StorageEngine | None = None,
    settings: PalmSettings | None = None,
    show_banner: bool = True,
) -> CliContext:
    """
    Open a CLI session backed by a bootstrapped :class:`~palm.app.app.PalmApp`.

    All runtime wiring (storage, ``InstanceManager``, hooks, definitions) is
    handled by :func:`~palm.app.session.create_cli_app`.
    """
    console = create_console()
    app = create_cli_app(
        storage_backend=storage_backend,
        data_dir=data_dir,
        storage=storage,
        settings=settings,
    )
    ctx = CliContext(app=app, console=console)
    if show_banner:
        print_startup_banner(console, app)
    return ctx


def shutdown_context(ctx: CliContext) -> None:
    ctx.app.shutdown()