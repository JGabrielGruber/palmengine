"""
CLI startup — application bootstrap and definition catalog loading.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from palm.app.app import PalmApp
from palm.app.settings import PalmSettings
from palm.common.exceptions import DefinitionNotFoundError
from palm.runtimes.cli_pkg.context import CliContext
from palm.runtimes.embedded import EmbeddedRuntime


def create_console() -> Any:
    try:
        from rich.console import Console

        return Console(highlight=False)
    except ImportError as exc:
        raise SystemExit(
            "Rich is required for the Palm CLI. Install with: uv sync --extra cli"
        ) from exc


def bootstrap_runtime(
    *,
    storage_backend: str = "memory",
    data_dir: Path | None = None,
    storage: Any | None = None,
) -> CliContext:
    """Start the CLI embedded runtime via :class:`~palm.app.app.PalmApp`."""
    settings = PalmSettings(storage_backend=storage_backend, data_dir=data_dir)
    app = PalmApp(settings, storage=storage)
    app.bootstrap()
    runtime = app.create_runtime(
        "embedded",
        name="cli",
        autostart=True,
        storage_backend=storage_backend,
    )
    app.load_definitions(name="cli")
    return CliContext(runtime=runtime, console=create_console(), app=app)


def shutdown_context(ctx: CliContext) -> None:
    if ctx.app is not None:
        ctx.app.shutdown()
    else:
        ctx.runtime.stop()


def resolve_flow_ref(runtime: EmbeddedRuntime, ref: str) -> Any:
    repo = runtime.repository
    try:
        return repo.get_flow(ref)
    except DefinitionNotFoundError:
        return repo.get_flow(ref, by_id=True)


def resolve_process_ref(runtime: EmbeddedRuntime, ref: str) -> Any:
    repo = runtime.repository
    try:
        return repo.get_process(ref)
    except DefinitionNotFoundError:
        return repo.get_process(ref, by_id=True)