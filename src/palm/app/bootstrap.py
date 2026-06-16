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


def host_profile_from_settings(settings: PalmSettings) -> HostProfile:
    """Resolve a :class:`~palm.app.host.roles.HostProfile` from application settings."""
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
