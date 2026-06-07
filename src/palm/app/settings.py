"""
PalmSettings — central configuration for Palm applications.

Loaded from environment variables (``PALM_*``) and optional ``.env`` files via
``pydantic-settings``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

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