"""
Palm configuration using Pydantic Settings.

Reads from environment variables and optional .env file.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class PalmSettings(BaseSettings):
    """Runtime configuration for the Palm engine."""

    model_config = SettingsConfigDict(
        env_prefix="PALM_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Paths
    data_dir: Path = Field(default=Path("data"))
    log_dir: Path = Field(default=Path("logs"))
    sqlite_db: str = Field(default="palm_sessions.db")

    # Session behavior
    default_session_ttl_seconds: int = Field(default=3600, ge=60)
    session_cleanup_interval_seconds: int = Field(default=300)

    # Concurrency
    max_concurrent_processes: int = Field(default=16, ge=1)
    default_process_timeout_seconds: int = Field(default=300)

    # CLI
    cli_prompt: str = Field(default="palm> ")
    cli_history_file: Path = Field(default=Path("~/.palm_history"))

    # Logging
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")  # "json" | "console"

    @property
    def db_path(self) -> Path:
        """Full path to the SQLite database file."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        return self.data_dir / self.sqlite_db

    @property
    def resolved_history_file(self) -> Path:
        """Expand ~ in history file path."""
        return self.cli_history_file.expanduser()


settings = PalmSettings()

__all__ = ["PalmSettings", "settings"]
