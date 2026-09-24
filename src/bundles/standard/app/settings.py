"""
PalmSettings — central configuration for Palm applications.

Base path reads ``PALM_*`` from ``os.environ`` only (stdlib). Optional
``.env`` / ``--config`` file load requires the ``dotenv`` extra.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, fields, replace
from pathlib import Path
from typing import Any, Literal, Mapping

SchedulerPolicy = Literal["inline", "queued"]

_ENV_PREFIX = "PALM_"
_SCHEDULER_POLICIES = frozenset({"inline", "queued"})

# Explicit parse kinds — postponed annotations make dataclass field types strings.
_FIELD_KIND: dict[str, str] = {
    "storage_backend": "str",
    "data_dir": "path|none",
    "observability": "bool",
    "auth_enforce": "bool",
    "auth_roles": "list[str]",
    "load_example_definitions": "bool",
    "default_scheduler": "scheduler",
    "queued_workers": "int",
    "max_concurrent_jobs": "int|none",
    "enable_state_snapshot": "bool",
    "snapshot_on_status": "list[str]",
    "max_snapshots_per_instance": "int",
    "max_loaded_instances": "int",
    "max_concurrent_active": "int",
    "reconcile_instances_on_startup": "bool",
    "host_profile": "str|none",
    "host_roles": "list[str]",
    "worker_count": "int",
    "server_host": "str",
    "server_port": "int",
    "outbox_poll_interval": "float",
    "work_plane_poll_interval": "float",
    "work_plane_batch_size": "int",
    "work_plane_max_depth": "int",
    "work_plane_workers": "int",
    "work_plane_lease_seconds": "float",
    "structure_definition_id": "str|none",
    "rebuild_projections_on_startup": "bool",
    "projection_rebuild_batch_size": "int",
    "projection_rebuild_max_instances": "int",
    "projection_rebuild_skip_if_fresh": "bool",
    "workload_host_enabled": "bool",
    "workload_default_runtime": "str|none",
    "session_strict_attribution": "bool",
    "webhook_urls": "list[str]",
    "webhook_event_types": "list[str]",
    "worker_ready_timeout": "float",
    "resource_cache_definitions": "bool",
    "resource_cache_results": "bool",
    "resource_cache_ttl_seconds": "float",
    "resource_cache_max_entries": "int",
    "analytics_enabled": "bool",
    "analytics_allow_unpublished": "bool",
    "analytics_allow_unpublished_with_server": "bool",
    "analytics_default_limit": "int",
    "analytics_max_limit": "int",
    "analytics_max_response_bytes": "int",
}


@dataclass(init=False)
class PalmSettings:
    """
    Application-wide Palm configuration.

    Environment prefix: ``PALM_`` (e.g. ``PALM_STORAGE_BACKEND=postgres``).
    Constructor kwargs and ``from_env_file`` overrides win over env.
    """

    storage_backend: str
    data_dir: Path | None
    observability: bool
    auth_enforce: bool
    auth_roles: list[str]
    load_example_definitions: bool
    default_scheduler: SchedulerPolicy
    # 0.62 — QueuedScheduler drive pool (default 1; needs exclusive drive)
    queued_workers: int
    max_concurrent_jobs: int | None
    enable_state_snapshot: bool
    snapshot_on_status: list[str]
    max_snapshots_per_instance: int
    max_loaded_instances: int
    max_concurrent_active: int
    reconcile_instances_on_startup: bool
    host_profile: str | None
    host_roles: list[str]
    worker_count: int
    server_host: str
    server_port: int
    # Outbox poll packaging. Loop membership is definition ``outbox``.
    outbox_poll_interval: float
    # Start-plane packaging (attach). Not work_drain membership.
    work_plane_poll_interval: float
    work_plane_batch_size: int
    work_plane_max_depth: int
    work_plane_workers: int
    work_plane_lease_seconds: float
    # 0.63.13 — explicit structure-definition seed from packaging/env.
    structure_definition_id: str | None
    rebuild_projections_on_startup: bool
    projection_rebuild_batch_size: int
    projection_rebuild_max_instances: int
    projection_rebuild_skip_if_fresh: bool
    # 0.56 — Workload plane: host subprocess runtime (default OFF)
    workload_host_enabled: bool
    workload_default_runtime: str | None
    # 0.58.15 — strict session attribution
    session_strict_attribution: bool
    webhook_urls: list[str]
    webhook_event_types: list[str]
    worker_ready_timeout: float
    resource_cache_definitions: bool
    resource_cache_results: bool
    resource_cache_ttl_seconds: float
    resource_cache_max_entries: int
    # Refines the install analytics organ (0.67.17). Not a composition seed.
    analytics_enabled: bool
    analytics_allow_unpublished: bool
    analytics_allow_unpublished_with_server: bool
    analytics_default_limit: int
    analytics_max_limit: int
    analytics_max_response_bytes: int

    def __init__(self, **kwargs: Any) -> None:
        values = _default_values()
        values.update(_environ_overrides())
        unknown = set(kwargs) - values.keys()
        if unknown:
            unknown_list = ", ".join(sorted(unknown))
            raise TypeError(
                f"PalmSettings() got unexpected keyword arguments: {unknown_list}"
            )
        values.update(kwargs)
        for name, value in values.items():
            setattr(self, name, value)

    @classmethod
    def for_tests(
        cls,
        *,
        load_examples: bool = False,
        full_recovery: bool = False,
    ) -> PalmSettings:
        """
        Lightweight settings for unit and integration tests.

        ``full_recovery`` enables projection rebuild and instance reconcile
        paths that dedicated recovery tests assert on. Outbox store wire
        follows DNA listing, not this flag.
        """
        return cls(
            load_example_definitions=load_examples,
            storage_backend="memory",
            rebuild_projections_on_startup=full_recovery,
            projection_rebuild_skip_if_fresh=True,
            projection_rebuild_batch_size=50,
            projection_rebuild_max_instances=200,
            worker_ready_timeout=0.5,
            outbox_poll_interval=5.0,
            reconcile_instances_on_startup=full_recovery,
        )

    @classmethod
    def from_env_file(cls, env_file: str | Path) -> PalmSettings:
        """Load settings with an explicit env file (used by CLI ``--config``).

        Requires the ``dotenv`` extra (``pip install 'palmengine[dotenv]'``).
        File values override ``PALM_*`` env for keys present in the file.
        """
        try:
            from dotenv import dotenv_values
        except ImportError as exc:
            raise RuntimeError(
                "PalmSettings.from_env_file requires the 'dotenv' extra "
                "(pip install 'palmengine[dotenv]')."
            ) from exc

        path = Path(env_file)
        if not path.is_file():
            raise FileNotFoundError(f"PalmSettings config file not found: {path}")

        raw = dotenv_values(path, encoding="utf-8")
        overrides = _parse_env_mapping(raw)
        return cls(**overrides)

    def definition_roots(self) -> list[Path]:
        """Directories scanned for ``register_definitions`` modules."""
        roots: list[Path] = []
        if self.data_dir is not None:
            roots.append(self.data_dir / "definitions")
        if self.load_example_definitions:
            roots.append(Path.cwd() / "examples" / "definitions")
        return roots


def copy_settings(settings: PalmSettings, **changes: Any) -> PalmSettings:
    """Return a shallow copy with optional field updates (``dataclasses.replace``)."""
    return replace(settings, **changes)


def _default_values() -> dict[str, Any]:
    return {
        "storage_backend": "memory",
        "data_dir": None,
        "observability": False,
        "auth_enforce": False,
        "auth_roles": ["user"],
        "load_example_definitions": True,
        "default_scheduler": "inline",
        "queued_workers": 1,
        "max_concurrent_jobs": None,
        "enable_state_snapshot": False,
        "snapshot_on_status": ["WAITING_FOR_INPUT", "SUCCEEDED", "FAILED"],
        "max_snapshots_per_instance": 10,
        "max_loaded_instances": 128,
        "max_concurrent_active": 32,
        "reconcile_instances_on_startup": True,
        "host_profile": None,
        "host_roles": [],
        "worker_count": 1,
        "server_host": "127.0.0.1",
        "server_port": 8080,
        "outbox_poll_interval": 0.5,
        "work_plane_poll_interval": 1.0,
        "work_plane_batch_size": 10,
        "work_plane_max_depth": 8,
        "work_plane_workers": 1,
        "work_plane_lease_seconds": 60.0,
        "structure_definition_id": None,
        "rebuild_projections_on_startup": True,
        "projection_rebuild_batch_size": 100,
        "projection_rebuild_max_instances": 5000,
        "projection_rebuild_skip_if_fresh": True,
        "workload_host_enabled": False,
        "workload_default_runtime": "local",
        "session_strict_attribution": True,
        "webhook_urls": [],
        "webhook_event_types": [],
        "worker_ready_timeout": 5.0,
        "resource_cache_definitions": True,
        "resource_cache_results": False,
        "resource_cache_ttl_seconds": 60.0,
        "resource_cache_max_entries": 256,
        "analytics_enabled": True,
        "analytics_allow_unpublished": False,
        "analytics_allow_unpublished_with_server": False,
        "analytics_default_limit": 1000,
        "analytics_max_limit": 10_000,
        "analytics_max_response_bytes": 2_000_000,
    }


def _environ_overrides() -> dict[str, Any]:
    return _parse_env_mapping(os.environ)


def _parse_env_mapping(raw: Mapping[str, str | None]) -> dict[str, Any]:
    overrides: dict[str, Any] = {}
    for name, kind in _FIELD_KIND.items():
        key = f"{_ENV_PREFIX}{name.upper()}"
        if key not in raw:
            continue
        value = raw[key]
        if value is None:
            continue
        overrides[name] = _parse_kind(name, kind, value)
    return overrides


def _parse_kind(name: str, kind: str, raw: str) -> Any:
    if kind == "str":
        return raw
    if kind == "str|none":
        return None if raw == "" else raw
    if kind == "bool":
        return _parse_bool(name, raw)
    if kind == "int":
        return _parse_int(name, raw)
    if kind == "int|none":
        return None if raw == "" else _parse_int(name, raw)
    if kind == "float":
        return _parse_float(name, raw)
    if kind == "path|none":
        return None if raw == "" else Path(raw)
    if kind == "list[str]":
        return _parse_str_list(name, raw)
    if kind == "scheduler":
        if raw not in _SCHEDULER_POLICIES:
            raise ValueError(
                f"Invalid PALM_{name.upper()}={raw!r}; expected one of "
                f"{sorted(_SCHEDULER_POLICIES)}"
            )
        return raw
    raise ValueError(f"Unsupported PalmSettings kind for {name}: {kind!r}")


def _parse_bool(name: str, raw: str) -> bool:
    lowered = raw.strip().lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    raise ValueError(
        f"Invalid PALM_{name.upper()}={raw!r}; expected 'true' or 'false'"
    )


def _parse_int(name: str, raw: str) -> int:
    try:
        return int(raw.strip())
    except ValueError as exc:
        raise ValueError(f"Invalid PALM_{name.upper()}={raw!r}; expected int") from exc


def _parse_float(name: str, raw: str) -> float:
    try:
        return float(raw.strip())
    except ValueError as exc:
        raise ValueError(
            f"Invalid PALM_{name.upper()}={raw!r}; expected float"
        ) from exc


def _parse_str_list(name: str, raw: str) -> list[str]:
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid PALM_{name.upper()}={raw!r}; expected JSON array of strings"
        ) from exc
    if not isinstance(parsed, list) or not all(isinstance(item, str) for item in parsed):
        raise ValueError(
            f"Invalid PALM_{name.upper()}={raw!r}; expected JSON array of strings"
        )
    return list(parsed)


# Keep field map aligned with the dataclass (guard for drift).
assert set(_FIELD_KIND) == {f.name for f in fields(PalmSettings)}
