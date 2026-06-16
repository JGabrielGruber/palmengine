"""
CLI startup — thin session opener delegating entirely to :mod:`palm.app.session`.
"""

from __future__ import annotations

from pathlib import Path

from palm.app.session import create_cli_host, create_console
from palm.app.settings import PalmSettings
from palm.core.storage import StorageEngine
from palm.runtimes.cli.shared.args import CliInvocation, settings_from_invocation
from palm.runtimes.cli.shared.context import CliContext
from palm.runtimes.cli.shared.startup import print_startup_banner


def bootstrap_runtime(
    *,
    storage_backend: str | None = None,
    data_dir: Path | None = None,
    storage: StorageEngine | None = None,
    settings: PalmSettings | None = None,
    invocation: CliInvocation | None = None,
    show_banner: bool = True,
    output_format: str = "table",
) -> CliContext:
    """
    Open a CLI session backed by a bootstrapped :class:`~palm.app.app.PalmApp`.

    All runtime wiring (storage, ``InstanceManager``, hooks, definitions) is
    handled by :func:`~palm.app.session.create_cli_app`.
    """
    console = create_console()
    resolved = settings_from_invocation(invocation) if invocation is not None else settings
    host = create_cli_host(
        storage_backend=storage_backend,
        data_dir=data_dir,
        storage=storage,
        settings=resolved,
    )
    fmt = invocation.output_format if invocation is not None else output_format
    ctx = CliContext(host=host, app=host.app, console=console, output_format=fmt)
    if show_banner:
        print_startup_banner(console, host.app)
    return ctx


def shutdown_context(ctx: CliContext) -> None:
    if ctx.host is not None and ctx.host.is_started:
        ctx.host.shutdown()
    else:
        ctx.app.shutdown()
