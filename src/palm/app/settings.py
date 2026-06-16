"""
PalmSettings — central configuration for Palm applications.

Loaded from environment variables (``PALM_*``) and optional ``.env`` files via
``pydantic-settings``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal, cast

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

SchedulerPolicy = Literal["inline", "queued"]


class PalmSettings(BaseSettings):
    """
    Application-wide Palm configuration.

    Environment prefix: ``PALM_`` (e.g. ``PALM_STORAGE_BACKEND=postgres``).
    """

    model_config = SettingsConfigDict(
        env_prefix="PALM_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    storage_backend: str = "memory"
    data_dir: Path | None = None
    observability: bool = False
    auth_enforce: bool = False
    auth_roles: list[str] = Field(default_factory=lambda: ["user"])
    load_example_definitions: bool = True
    default_scheduler: SchedulerPolicy = "inline"
    max_concurrent_jobs: int | None = None
    enable_state_snapshot: bool = False
    snapshot_on_status: list[str] = Field(
        default_factory=lambda: ["WAITING_FOR_INPUT", "SUCCEEDED", "FAILED"]
    )
    max_snapshots_per_instance: int = 10
    max_loaded_instances: int = 128
    max_concurrent_active: int = 32
    reconcile_instances_on_startup: bool = True
    host_profile: str | None = None
    host_roles: list[str] = Field(default_factory=list)
    worker_count: int = 1
    server_host: str = "127.0.0.1"
    server_port: int = 8080
    enable_outbox_service: bool = True
    outbox_poll_interval: float = 0.5
    enable_event_outbox: bool = True

    @classmethod
    def from_env_file(cls, env_file: str | Path) -> PalmSettings:
        """Load settings with an explicit env file (used by CLI ``--config``)."""
        configured = type(
            "_PalmSettingsFromFile",
            (cls,),
            {
                "model_config": SettingsConfigDict(
                    env_prefix="PALM_",
                    env_file=str(env_file),
                    env_file_encoding="utf-8",
                    extra="ignore",
                )
            },
        )
        return cast(PalmSettings, configured())

    def definition_roots(self) -> list[Path]:
        """Directories scanned for ``register_definitions`` modules."""
        roots: list[Path] = []
        if self.data_dir is not None:
            roots.append(self.data_dir / "definitions")
        roots.extend(
            [
                Path.cwd() / "examples" / "definitions",
            ]
        )
        return roots
