"""
Application bootstrap — plugin loading and definition catalog hydration.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import palm.patterns  # — autoload pattern apps
import palm.providers  # — autoload provider apps
import palm.storages  # noqa: F401 — autoload storage apps
from palm.app.settings import PalmSettings
from palm.common.persistence.definition_repository import DefinitionRepository


def ensure_plugins() -> None:
    """Import extensible plugin packages so registries are populated."""
    # Side-effect imports above register patterns, providers, and storages.
    return None


def hydrate_definitions_from_storage(repository: DefinitionRepository) -> int:
    """Load flow/process definitions from storage into the in-memory cache."""
    count = 0
    for flow in repository.list_flows():
        repository.register_flow(flow)
        count += 1
    for process in repository.list_processes():
        repository.register_process(process)
        count += 1
    return count


def load_definition_modules(
    repository: DefinitionRepository,
    *,
    roots: list[Path],
) -> int:
    """Import ``register_definitions`` modules from the given directories."""
    loaded = 0
    seen: set[Path] = set()
    for root in roots:
        if not root.is_dir():
            continue
        for path in sorted(root.glob("*.py")):
            if path.name.startswith("_") or path in seen:
                continue
            seen.add(path)
            if _import_register(path, repository):
                loaded += 1
    return loaded


def package_definition_roots(settings: PalmSettings) -> list[Path]:
    """Built-in example definition paths bundled with Palm."""
    if not settings.load_example_definitions:
        return []
    package_root = Path(__file__).resolve().parents[3]
    return [package_root / "examples" / "definitions"]


def all_definition_roots(settings: PalmSettings) -> list[Path]:
    """Merge configured, cwd, and packaged definition directories."""
    roots: list[Path] = []
    if settings.data_dir is not None:
        roots.append(settings.data_dir / "definitions")
    roots.append(Path.cwd() / "examples" / "definitions")
    roots.extend(package_definition_roots(settings))
    # Preserve order while deduplicating
    unique: list[Path] = []
    seen: set[Path] = set()
    for root in roots:
        resolved = root.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(root)
    return unique


def load_definitions_for_repository(
    repository: DefinitionRepository,
    settings: PalmSettings,
) -> int:
    """Hydrate storage-backed definitions and import code-defined catalogs."""
    count = hydrate_definitions_from_storage(repository)
    count += load_definition_modules(repository, roots=all_definition_roots(settings))
    return count


def runtime_start_options(settings: PalmSettings, **overrides: Any) -> dict[str, Any]:
    """Build keyword arguments for :meth:`~palm.runtimes.base.BaseRuntime.start`."""
    options: dict[str, Any] = {
        "storage_backend": settings.storage_backend,
        "observability": settings.observability,
        "auth_enforce": settings.auth_enforce,
        "auth_roles": list(settings.auth_roles),
    }
    if settings.max_concurrent_jobs is not None:
        options["max_concurrent_jobs"] = settings.max_concurrent_jobs
    options.update(overrides)
    return options


def _import_register(path: Path, repository: DefinitionRepository) -> bool:
    spec = importlib.util.spec_from_file_location(f"palm_app_definitions_{path.stem}", path)
    if spec is None or spec.loader is None:
        return False
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    register = getattr(module, "register_definitions", None)
    if not callable(register):
        return False
    register(repository)
    return True