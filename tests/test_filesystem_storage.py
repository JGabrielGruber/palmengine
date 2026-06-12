"""Tests for the production filesystem storage backend and StorageFactory."""

from __future__ import annotations

import json
import threading
from pathlib import Path

import pytest

from palm.app import PalmApp, PalmSettings
from palm.common import DefinitionRepository, InstanceRepository
from palm.common.storage import StorageFactory
from palm.core import (
    ConfigurationError,
    StorageEngine,
    storage_registry,
)
from palm.instances import ProcessInstance
from palm.storages.filesystem import FilesystemStorageBackend
from tests.test_definitions_storage import _sample_flow, _sample_process


def test_filesystem_registry_registration() -> None:
    assert "filesystem" in storage_registry.names()
    assert storage_registry.get("filesystem") is FilesystemStorageBackend


def test_filesystem_namespace_paths_and_json_roundtrip(tmp_path: Path) -> None:
    backend = FilesystemStorageBackend(data_dir=tmp_path)
    backend.open()
    payload = {"instance_id": "inst-1", "status": "PENDING", "count": 2}
    backend.set("palm:instances:inst-1", payload)

    stored = tmp_path / "palm" / "instances" / "inst-1.json"
    assert stored.exists()
    assert json.loads(stored.read_text(encoding="utf-8")) == payload
    assert backend.get("palm:instances:inst-1") == payload

    backend.delete("palm:instances:inst-1")
    assert backend.get("palm:instances:inst-1") is None
    backend.close()


def test_filesystem_atomic_write_replaces_existing(tmp_path: Path) -> None:
    backend = FilesystemStorageBackend(data_dir=tmp_path)
    backend.open()
    key = "palm:definitions:index:flow"
    backend.set(key, ["flow-a"])
    path = tmp_path / "palm" / "definitions" / "index" / "flow.json"
    assert path.read_text(encoding="utf-8") == '["flow-a"]'

    backend.set(key, ["flow-a", "flow-b"])
    assert json.loads(path.read_text(encoding="utf-8")) == ["flow-a", "flow-b"]
    assert not list(path.parent.glob("*.tmp"))
    backend.close()


def test_filesystem_missing_and_corrupted_payloads(tmp_path: Path) -> None:
    backend = FilesystemStorageBackend(data_dir=tmp_path)
    backend.open()
    assert backend.get("palm:instances:missing") is None

    corrupt = tmp_path / "palm" / "instances" / "broken.json"
    corrupt.parent.mkdir(parents=True)
    corrupt.write_text("{not-json", encoding="utf-8")
    assert backend.get("palm:instances:broken") is None
    backend.close()


def test_filesystem_reads_legacy_v06_flat_files(tmp_path: Path) -> None:
    backend = FilesystemStorageBackend(data_dir=tmp_path)
    legacy = tmp_path / "palm:instances:legacy-1"
    legacy.write_text(
        json.dumps({"instance_id": "legacy-1", "status": "SUCCEEDED"}),
        encoding="utf-8",
    )
    backend.open()
    assert backend.get("palm:instances:legacy-1") == {
        "instance_id": "legacy-1",
        "status": "SUCCEEDED",
    }
    backend.close()


def test_filesystem_rejects_invalid_data_dir(tmp_path: Path) -> None:
    file_path = tmp_path / "not-a-dir"
    file_path.write_text("x", encoding="utf-8")
    with pytest.raises(ConfigurationError):
        FilesystemStorageBackend(data_dir=file_path)


def test_filesystem_thread_safe_writes(tmp_path: Path) -> None:
    backend = FilesystemStorageBackend(data_dir=tmp_path)
    backend.open()
    errors: list[Exception] = []

    def worker(index: int) -> None:
        try:
            backend.set(f"palm:instances:inst-{index}", {"index": index})
            assert backend.get(f"palm:instances:inst-{index}") == {"index": index}
        except Exception as exc:  # pragma: no cover - surfaced after join
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert errors == []
    backend.close()


def test_storage_factory_backend_options_for_filesystem() -> None:
    options = StorageFactory.backend_options(
        storage_backend="filesystem",
        data_dir=Path("/tmp/palm-data"),
    )
    assert options["data_dir"] == Path("/tmp/palm-data")

    defaults = StorageFactory.backend_options(storage_backend="filesystem")
    assert defaults["data_dir"] == Path("data")


def test_storage_factory_lazy_loads_mongodb() -> None:
    StorageFactory.ensure_registered("mongodb")
    assert "mongodb" in storage_registry.names()

    engine = StorageEngine()
    StorageFactory.initialize_engine(engine, storage_backend="mongodb")
    engine.set("token", "abc")
    assert engine.get("token") == "abc"
    engine.shutdown()


def test_definition_repository_filesystem_roundtrip(tmp_path: Path) -> None:
    engine = StorageEngine()
    StorageFactory.initialize_engine(
        engine,
        storage_backend="filesystem",
        data_dir=tmp_path,
    )
    repo = DefinitionRepository(engine)
    repo.save_flow(_sample_flow())
    repo.save_process(_sample_process())

    fresh = DefinitionRepository(engine)
    flow = fresh.get_flow_by_name("onboard")
    process = fresh.get_process_by_name("onboarding")
    assert flow.definition_id == "flow-onboard-1"
    assert process.definition_id == "proc-onboard-1"
    engine.shutdown()


def test_instance_repository_filesystem_roundtrip(tmp_path: Path) -> None:
    engine = StorageEngine()
    StorageFactory.initialize_engine(
        engine,
        storage_backend="filesystem",
        data_dir=tmp_path,
    )
    repo = InstanceRepository(engine)
    inst = ProcessInstance(
        instance_id="inst-fs-1",
        job_id="job-fs-1",
        status="WAITING_FOR_INPUT",
        state_snapshot={"k": 1},
        flow_definition={"name": "f", "pattern": "wizard", "options": {}},
        pattern="wizard",
    )
    repo.save(inst)

    fresh = InstanceRepository(engine)
    loaded = fresh.get("inst-fs-1")
    assert loaded.job_id == "job-fs-1"
    assert loaded.state_snapshot["k"] == 1
    engine.shutdown()


def test_palm_app_filesystem_integration(tmp_path: Path) -> None:
    settings = PalmSettings(storage_backend="filesystem", data_dir=tmp_path)
    with PalmApp(settings) as app:
        app.create_runtime("embedded", autostart=True)
        runtime = app.runtime()
        runtime.repository.save_flow(_sample_flow())
        runtime.instances.save(
            ProcessInstance(
                instance_id="inst-app-1",
                job_id="job-app-1",
                status="PENDING",
                state_snapshot={},
                flow_definition=_sample_flow().to_dict(),
                pattern="wizard",
            )
        )
        assert app.list_flows()[0].name == "onboard"
        assert app.list_instances()[0].instance_id == "inst-app-1"
