"""
Application bootstrap — plugin loading and definition catalog hydration.
"""

from __future__ import annotations

import importlib.util
from dataclasses import replace
from pathlib import Path
from typing import Any

import palm.common.transforms  # autoload common transform rules
import palm.patterns  # — autoload pattern apps
import palm.providers  # — autoload provider apps
import palm.storages  # noqa: F401 — autoload core storage apps
from palm.app.host.roles import HostProfile
from palm.app.settings import PalmSettings
from palm.common.persistence.definition_repository import DefinitionRepository
from palm.common.storage import StorageFactory


def ensure_plugins() -> None:
    """Import extensible plugin packages so registries are populated."""
    # Side-effect imports above register transforms, patterns, providers, and storages.
    return None


def hydrate_definitions_from_storage(repository: DefinitionRepository) -> int:
    """Load flow/process/resource definitions from storage into the in-memory cache."""
    count = 0
    for flow in repository.list_flows():
        repository.register_flow(flow)
        count += 1
    for process in repository.list_processes():
        repository.register_process(process)
        count += 1
    for resource in repository.list_resources():
        repository.register_resource(resource)
        count += 1
    return count


def load_definition_modules(
    repository: DefinitionRepository,
    *,
    roots: list[Path],
) -> int:
    """Import ``register_definitions`` from flat modules and packages under roots.

    Discovery (per root, sorted by name):

    1. **Packages** — ``name/__init__.py`` with ``register_definitions`` (preferred
       for multi-file examples: resources then flows ordered in ``__init__``).
    2. **Flat modules** — ``name.py`` (legacy single-file demos).

    Package import path is ``examples.definitions.<name>`` when the root is
    ``…/examples/definitions``; otherwise ``<name>`` with the root on ``sys.path``.
    """
    import importlib
    import sys

    loaded = 0
    seen: set[Path] = set()
    for root in roots:
        if not root.is_dir():
            continue
        root = root.resolve()
        # Packages first (explicit multi-module examples)
        for child in sorted(root.iterdir(), key=lambda p: p.name):
            if not child.is_dir() or child.name.startswith(("_", ".")):
                continue
            init = child / "__init__.py"
            if not init.is_file() or child in seen:
                continue
            seen.add(child)
            if _import_package_register(child, root, repository):
                loaded += 1
        # Flat single-file modules
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


def host_profile_from_settings(settings: PalmSettings) -> HostProfile:
    """Resolve a :class:`~palm.app.host.roles.HostProfile` from application settings.

    Always applies ``server_host`` / ``server_port`` from settings so
    ``PALM_SERVER_HOST`` / ``PALM_SERVER_PORT`` win over dataclass defaults
    (presets like ``server`` and ``all_in_one`` used to ignore them).
    """
    if settings.host_profile:
        profile = HostProfile.from_preset(settings.host_profile)
    elif settings.host_roles:
        profile = HostProfile.from_roles(
            settings.host_roles,
            worker_count=settings.worker_count,
            server_host=settings.server_host,
            server_port=settings.server_port,
            enable_outbox_service=settings.enable_outbox_service,
            outbox_poll_interval=settings.outbox_poll_interval,
        )
    else:
        profile = HostProfile.all_in_one()
    return replace(
        profile,
        enable_outbox_service=settings.enable_outbox_service,
        outbox_poll_interval=settings.outbox_poll_interval,
        server_host=settings.server_host,
        server_port=settings.server_port,
    )


def runtime_start_options(settings: PalmSettings, **overrides: Any) -> dict[str, Any]:
    """Build keyword arguments for :meth:`~palm.common.runtimes.base.BaseRuntime.start`."""
    options: dict[str, Any] = {
        "storage_backend": settings.storage_backend,
        "backend_options": StorageFactory.backend_options(settings=settings),
        "observability": settings.observability,
        "auth_enforce": settings.auth_enforce,
        "auth_roles": list(settings.auth_roles),
        "scheduler": settings.default_scheduler,
        "enable_event_outbox": settings.enable_event_outbox,
    }
    if settings.max_concurrent_jobs is not None:
        options["max_concurrent_jobs"] = settings.max_concurrent_jobs
    options["enable_state_snapshot"] = settings.enable_state_snapshot
    options["snapshot_on_status"] = list(settings.snapshot_on_status)
    options["max_snapshots_per_instance"] = settings.max_snapshots_per_instance
    options["max_loaded_instances"] = settings.max_loaded_instances
    options["max_concurrent_active"] = settings.max_concurrent_active
    options["reconcile_on_startup"] = settings.reconcile_instances_on_startup
    options["resource_cache"] = {
        "cache_definitions": settings.resource_cache_definitions,
        "cache_results": settings.resource_cache_results,
        "ttl_seconds": settings.resource_cache_ttl_seconds,
        "max_entries": settings.resource_cache_max_entries,
    }
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


def _import_package_register(
    package_dir: Path,
    definitions_root: Path,
    repository: DefinitionRepository,
) -> bool:
    """Import ``examples.definitions.<pkg>`` (or bare pkg) and call register_definitions."""
    import importlib
    import sys

    definitions_root = definitions_root.resolve()
    package_dir = package_dir.resolve()
    pkg_name = package_dir.name

    # Prefer full path when root is …/examples/definitions
    module_name: str
    if definitions_root.name == "definitions" and definitions_root.parent.name == "examples":
        project_root = definitions_root.parent.parent
        root_s = str(project_root)
        if root_s not in sys.path:
            sys.path.insert(0, root_s)
        module_name = f"examples.definitions.{pkg_name}"
    else:
        root_s = str(definitions_root)
        if root_s not in sys.path:
            sys.path.insert(0, root_s)
        module_name = pkg_name

    try:
        module = importlib.import_module(module_name)
    except Exception:
        # Reload if partially imported
        if module_name in sys.modules:
            del sys.modules[module_name]
        try:
            module = importlib.import_module(module_name)
        except Exception:
            return False

    register = getattr(module, "register_definitions", None)
    if not callable(register):
        return False
    register(repository)
    return True
