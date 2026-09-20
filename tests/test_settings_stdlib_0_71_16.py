"""0.71.16 — stdlib PalmSettings; file load via dotenv extra (fail closed)."""

from __future__ import annotations

import dataclasses
import importlib
import sys
from pathlib import Path
from typing import Any

import pytest

from palm.app.cli_settings import resolve_cli_settings
from palm.app.settings import PalmSettings
from tests.fast_settings import make_test_settings


def test_palm_settings_reads_palm_env_without_pydantic(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PALM_STORAGE_BACKEND", "filesystem")
    monkeypatch.setenv("PALM_ENABLE_STATE_SNAPSHOT", "true")
    monkeypatch.setenv("PALM_QUEUED_WORKERS", "3")
    monkeypatch.setenv("PALM_SERVER_PORT", "9090")
    monkeypatch.setenv("PALM_OUTBOX_POLL_INTERVAL", "1.5")
    monkeypatch.setenv("PALM_AUTH_ROLES", '["admin","ops"]')

    settings_mod = importlib.import_module("palm.app.settings")
    assert getattr(settings_mod, "BaseSettings", None) is None
    assert "pydantic" not in settings_mod.__dict__
    assert "pydantic_settings" not in settings_mod.__dict__

    settings = PalmSettings()
    assert settings.storage_backend == "filesystem"
    assert settings.enable_state_snapshot is True
    assert settings.queued_workers == 3
    assert settings.server_port == 9090
    assert settings.outbox_poll_interval == 1.5
    assert settings.auth_roles == ["admin", "ops"]
    assert dataclasses.is_dataclass(settings)


def test_palm_settings_module_has_no_pydantic_imports() -> None:
    source = Path("src/palm/app/settings.py").read_text(encoding="utf-8")
    assert "pydantic" not in source
    assert "BaseSettings" not in source


def test_no_cwd_dotenv_autoload(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("PALM_STORAGE_BACKEND", raising=False)
    (tmp_path / ".env").write_text("PALM_STORAGE_BACKEND=filesystem\n", encoding="utf-8")

    settings = PalmSettings()
    assert settings.storage_backend == "memory"


def test_from_env_file_without_dotenv_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env_path = tmp_path / "palm.env"
    env_path.write_text("PALM_STORAGE_BACKEND=filesystem\n", encoding="utf-8")

    real_import = __import__

    def _hide_dotenv(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "dotenv" or name.startswith("dotenv."):
            raise ImportError("mocked missing python-dotenv")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", _hide_dotenv)
    # Also clear a cached import if present.
    monkeypatch.delitem(sys.modules, "dotenv", raising=False)
    monkeypatch.delitem(sys.modules, "dotenv.main", raising=False)

    with pytest.raises((ImportError, RuntimeError, ModuleNotFoundError)) as excinfo:
        PalmSettings.from_env_file(env_path)

    message = str(excinfo.value).lower()
    assert "dotenv" in message


def test_from_env_file_applies_file_over_env_then_cli_wins(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pytest.importorskip("dotenv")

    monkeypatch.setenv("PALM_STORAGE_BACKEND", "memory")
    monkeypatch.setenv("PALM_SERVER_PORT", "8080")
    monkeypatch.delenv("PALM_DATA_DIR", raising=False)

    env_path = tmp_path / "palm.env"
    env_path.write_text(
        "\n".join(
            [
                "PALM_STORAGE_BACKEND=filesystem",
                f"PALM_DATA_DIR={tmp_path / 'data'}",
                "PALM_SERVER_PORT=9090",
                "",
            ]
        ),
        encoding="utf-8",
    )

    from_file = PalmSettings.from_env_file(env_path)
    assert from_file.storage_backend == "filesystem"
    assert from_file.data_dir == tmp_path / "data"
    assert from_file.server_port == 9090

    merged = resolve_cli_settings(
        settings=from_file,
        storage_backend="mongodb",
        max_loaded_instances=7,
    )
    assert merged.storage_backend == "mongodb"
    assert merged.server_port == 9090
    assert merged.max_loaded_instances == 7
    assert merged.data_dir == tmp_path / "data"


def test_env_parse_fails_closed_on_garbage(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PALM_QUEUED_WORKERS", "not-an-int")
    with pytest.raises(ValueError):
        PalmSettings()


def test_for_tests_and_replace_keep_helpers_green(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("PALM_STORAGE_BACKEND", raising=False)
    base = PalmSettings.for_tests(load_examples=False)
    assert base.storage_backend == "memory"
    assert base.load_example_definitions is False

    updated = dataclasses.replace(base, analytics_default_limit=42)
    assert updated.analytics_default_limit == 42
    assert base.analytics_default_limit == 1000

    helper = make_test_settings(storage_backend="filesystem", data_dir=Path("/tmp/palm-x"))
    assert helper.storage_backend == "filesystem"
    assert helper.data_dir == Path("/tmp/palm-x")
    assert not hasattr(helper, "model_copy")


def test_src_palm_has_no_pydantic_imports() -> None:
    root = Path("src/palm")
    offenders: list[str] = []
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "pydantic" in text or "pydantic_settings" in text:
            offenders.append(str(path))
    assert offenders == []
