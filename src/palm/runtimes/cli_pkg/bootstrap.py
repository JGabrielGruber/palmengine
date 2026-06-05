"""
CLI startup — runtime initialization and definition catalog loading.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import palm.patterns  # noqa: F401
import palm.providers  # noqa: F401
import palm.storages  # noqa: F401

from palm.core.storage import StorageEngine
from palm.executions.exceptions import DefinitionNotFoundError
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
    backend: str = "memory",
    data_dir: Path | None = None,
    storage: StorageEngine | None = None,
) -> CliContext:
    """Start embedded runtime and hydrate definition/instance indexes from storage."""
    runtime = EmbeddedRuntime(storage=storage)
    runtime.start(backend=backend)
    _hydrate_definitions_from_storage(runtime)
    _load_example_definitions(runtime, data_dir)
    return CliContext(runtime=runtime, console=create_console())


def shutdown_context(ctx: CliContext) -> None:
    ctx.runtime.stop()


def _hydrate_definitions_from_storage(runtime: EmbeddedRuntime) -> None:
    repo = runtime.repository
    for flow in repo.list_flows():
        repo.register_flow(flow)
    for process in repo.list_processes():
        repo.register_process(process)


def _load_example_definitions(runtime: EmbeddedRuntime, data_dir: Path | None) -> None:
    roots = [
        Path(__file__).resolve().parents[4] / "examples" / "definitions",
        Path.cwd() / "examples" / "definitions",
    ]
    if data_dir is not None:
        roots.insert(0, data_dir / "definitions")

    seen: set[Path] = set()
    for root in roots:
        if not root.is_dir():
            continue
        for path in sorted(root.glob("*.py")):
            if path.name.startswith("_") or path in seen:
                continue
            seen.add(path)
            _import_register(path, runtime.repository)


def _import_register(path: Path, repository: Any) -> None:
    spec = importlib.util.spec_from_file_location(f"palm_examples_{path.stem}", path)
    if spec is None or spec.loader is None:
        return
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    register = getattr(module, "register_definitions", None)
    if callable(register):
        register(repository)


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