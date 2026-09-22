"""Hermetic run directory staging (0.54.8)."""

from __future__ import annotations

from pathlib import Path

import pytest

from plugins.runners.neonroot.run_dir import (
    create_run_dir,
    remove_run_dir,
    write_payload_file,
)


def test_create_run_dir_layout(tmp_path: Path) -> None:
    run = create_run_dir(data_dir=tmp_path, run_id="abc123", meta={"purpose": "test"})
    assert run.root.is_dir()
    assert run.payload.is_dir()
    assert run.input.is_dir()
    assert run.output.is_dir()
    assert run.meta_path.is_file()
    assert "abc123" in run.meta_path.read_text(encoding="utf-8")


def test_write_payload_and_spawn_params(tmp_path: Path) -> None:
    run = create_run_dir(data_dir=tmp_path)
    path = write_payload_file(run, "main.py", "print('hi')\n")
    assert path.read_text(encoding="utf-8").startswith("print")
    params = run.neonroot_spawn_params(
        image="palm-ci",
        command=["python", "payload/main.py"],
        vault="palm-ci",
    )
    assert params["seed_mode"] == "bind"
    assert params["seed"] == str(run.root.resolve())
    assert params["image"] == "palm-ci"


def test_write_payload_rejects_traversal(tmp_path: Path) -> None:
    run = create_run_dir(data_dir=tmp_path)
    with pytest.raises(ValueError):
        write_payload_file(run, "../x.py", "nope")


def test_remove_run_dir(tmp_path: Path) -> None:
    run = create_run_dir(data_dir=tmp_path, run_id="toreap")
    assert run.root.exists()
    remove_run_dir(run)
    assert not run.root.exists()
