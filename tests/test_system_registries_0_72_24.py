"""Bound-runtime reads use the seat the caller already holds (0.72.24).

File invoke reads the storage engine on the resource engine. Wait open and
close read the continue plane and the orchestration on the pattern build.
Authoring ``bound`` reads the definitions service the host passed in.
``get_bound_runtime()`` is not a fallback for those reads.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from bundles.minimal.bind import bind_memory
from bundles.minimal.runtime import MinimalRuntime
from drivers.storages.filesystem.backend import FilesystemBackend
from plugins.kits.authoring import bound
from plugins.patterns.wizard.bindings.definitions.builder import build
from plugins.patterns.wizard.flow.phases.resource import WizardResourceLeaf
from plugins.patterns.wizard.pattern import WizardPattern
from plugins.providers.authoring.provider import AuthoringProvider
from plugins.providers.file.provider import FileProvider

from palm.common.patterns.build_context import PatternBuildContext
from palm.common.providers._registry import register_runtime_accessor
from palm.core.behavior_tree import PatternStatus
from palm.core.orchestration import Job
from palm.core.registry import Registry
from palm.core.resource.engine import ResourceEngine
from palm.core.resource.result import ProviderResult
from palm.core.storage.engine import StorageEngine
from palm.core.wait import WAIT_KIND_JOB, has_open_waits, make_job_wait
from palm.definitions.flow import FlowDefinition
from palm.system.registries import SystemRegistries
from palm.system.subsystems.planes.wait import WaitPlaneService
from palm.system.subsystems.planes.wait.access import (
    find_job_for_state,
    open_interest_for_state,
)


class _Definitions:
    def __init__(self) -> None:
        self.names: list[str] = []

    def create_flow(self, body: dict[str, Any]) -> dict[str, Any]:
        name = str(body.get("name"))
        self.names.append(name)
        return {"name": name}

    def create_resource(self, body: dict[str, Any]) -> dict[str, Any]:
        name = str(body.get("name"))
        self.names.append(name)
        return {"name": name}


class _Invoker:
    is_initialized = True

    def initialize(self, **options: Any) -> None:
        del options

    def invoke(self, *args: Any, **kwargs: Any) -> ProviderResult:
        del args, kwargs
        return ProviderResult.ok(
            {
                "nested_park": True,
                "child_job_id": "child-1",
                "job_id": "child-1",
            },
            nested_park=True,
        )


class _Jobs:
    def __init__(self, job: Job) -> None:
        self._job = job

    @property
    def jobs(self) -> dict[str, Job]:
        return {self._job.id: self._job}


@pytest.fixture
def _accessor() -> Any:
    import palm.common.providers._registry as provider_registry

    state: dict[str, Any] = {"calls": [], "saved": None, "on": False}

    def install() -> list[str]:
        def read() -> None:
            state["calls"].append("read")
            return None

        with provider_registry._lock:
            state["saved"] = provider_registry._runtime_accessor
        register_runtime_accessor(read)
        state["on"] = True
        return state["calls"]

    try:
        yield install
    finally:
        if state["on"]:
            with provider_registry._lock:
                provider_registry._runtime_accessor = state["saved"]


def _filesystem(path: Path) -> StorageEngine:
    backend = FilesystemBackend(name="filesystem", data_dir=path)
    backend.open()
    engine = StorageEngine()
    engine.attach(backend)
    return engine


def _resource(
    *providers: tuple[str, type],
    storage: StorageEngine | None = None,
    definitions: _Definitions | None = None,
) -> ResourceEngine:
    engine = ResourceEngine()
    table: Registry[Any] = Registry("provider")
    for name, cls in providers:
        table.register(name, cls)
    engine.bind_registry(table)
    if storage is not None:
        engine.bind_storage(storage)
    if definitions is not None:
        engine.bind_definitions(definitions)
    engine.initialize()
    return engine


def _stop(*runtimes: MinimalRuntime) -> None:
    for runtime in runtimes:
        if runtime.is_started:
            runtime.stop()


def test_file_invoke_reads_the_caller_storage(tmp_path: Path, _accessor: Any) -> None:
    calls = _accessor()
    first_root = tmp_path / "a"
    second_root = tmp_path / "b"
    explicit = tmp_path / "explicit"
    first = _resource(("file", FileProvider), storage=_filesystem(first_root))
    second = _resource(("file", FileProvider), storage=_filesystem(second_root))
    bare = _resource(("file", FileProvider))

    left = first.invoke(
        provider="file",
        action="write",
        resource_id="note.json",
        params={"content": {"n": 1}},
    )
    right = second.invoke(
        provider="file",
        action="write",
        resource_id="note.json",
        params={"content": {"n": 2}},
    )
    pinned = first.invoke(
        provider="file",
        action="write",
        resource_id="pinned.json",
        params={"content": {"n": 3}, "documents_root": str(explicit)},
    )
    missing = bare.invoke(
        provider="file",
        action="exists",
        resource_id="missing.json",
    )

    assert left.success is True
    assert right.success is True
    assert left.data["documents_root"] == str((first_root / "documents").resolve())
    assert right.data["documents_root"] == str((second_root / "documents").resolve())
    assert (first_root / "documents" / "note.json").is_file()
    assert (second_root / "documents" / "note.json").is_file()
    assert pinned.success is True
    assert pinned.data["documents_root"] == str(explicit.resolve())
    assert missing.success is True
    assert missing.data["documents_root"] == str((Path("data") / "documents").resolve())
    assert calls == []


def test_wait_open_reads_the_caller_plane(_accessor: Any) -> None:
    calls = _accessor()
    first_job = Job(id="owner-a", executable=None)
    second_job = Job(id="owner-b", executable=None)
    first_plane = WaitPlaneService()
    second_plane = WaitPlaneService()
    first = _park(first_job, first_plane)
    second = _park(second_job, second_plane)

    assert first.tick(first_job.state) is PatternStatus.WAITING_FOR_INPUT
    assert second.tick(second_job.state) is PatternStatus.WAITING_FOR_INPUT
    assert first_job.id in first_plane.index.owners_for(
        kind=WAIT_KIND_JOB,
        target_id="child-1",
    )
    assert second_job.id in second_plane.index.owners_for(
        kind=WAIT_KIND_JOB,
        target_id="child-1",
    )
    assert first_job.id not in second_plane.index.owners_for(
        kind=WAIT_KIND_JOB,
        target_id="child-1",
    )
    assert calls == []


def test_wait_open_without_a_plane_skips_the_accessor(_accessor: Any) -> None:
    calls = _accessor()
    job = Job(id="owner-c", executable=None)
    opened = open_interest_for_state(job.state, make_job_wait("child-x"))
    assert opened.target_id == "child-x"
    assert has_open_waits(job.state)
    assert find_job_for_state(job.state) is None
    assert calls == []


def test_pattern_build_carries_the_runtime_seats(_accessor: Any) -> None:
    calls = _accessor()
    first = MinimalRuntime()
    second = MinimalRuntime()
    first.start(drivers=bind_memory(), structure_definition_id="local.embedded")
    second.start(drivers=bind_memory(), structure_definition_id="local.embedded")
    try:
        left = first.executor._build_context()
        right = second.executor._build_context()
        assert left.wait_plane is first.wait_plane
        assert right.wait_plane is second.wait_plane
        assert left.wait_plane is not right.wait_plane
        assert left.orchestration is first.orchestration
        assert right.orchestration is second.orchestration
        assert calls == []
    finally:
        _stop(first, second)


def test_authoring_reads_the_caller_definitions(_accessor: Any) -> None:
    calls = _accessor()
    first = _Definitions()
    second = _Definitions()
    assert bound(definitions=first).commit({"name": "direct-a"})["name"] == "direct-a"
    assert bound(definitions=second).commit({"name": "direct-b"})["name"] == "direct-b"

    left = _resource(("authoring", AuthoringProvider), definitions=first)
    right = _resource(("authoring", AuthoringProvider), definitions=second)
    published = left.invoke(
        provider="authoring",
        action="commit",
        params={"body": {"name": "engine-a"}},
    )
    other = right.invoke(
        provider="authoring",
        action="commit",
        params={"body": {"name": "engine-b"}},
    )
    bare = _resource(("authoring", AuthoringProvider))
    missed = bare.invoke(
        provider="authoring",
        action="commit",
        params={"body": {"name": "missing"}},
    )

    assert published.success is True
    assert other.success is True
    assert first.names == ["direct-a", "engine-a"]
    assert second.names == ["direct-b", "engine-b"]
    assert missed.success is False
    assert "no bound definitions" in str(missed.error)
    with pytest.raises(RuntimeError, match="no bound definitions"):
        bound()
    assert calls == []


def _park(job: Job, plane: WaitPlaneService) -> WizardPattern:
    registries = SystemRegistries()
    steps = Registry("wizard step")
    steps.register("resource", WizardResourceLeaf)
    registries.install("wizard_step", steps)
    flow = FlowDefinition(
        name=f"park-{job.id}",
        pattern="wizard",
        options={
            "steps": [
                {
                    "slug": "spawn",
                    "step_kind": "resource",
                    "resource_ref": "sub",
                    "output_key": "child_job",
                    "title": "Spawn",
                    "prompt": "?",
                }
            ]
        },
    )
    context = PatternBuildContext(
        registries=registries,
        resource_engine=_Invoker(),  # type: ignore[arg-type]
        wait_plane=plane,
        orchestration=_Jobs(job),
    )
    built = build(flow, context, WizardPattern)
    assert isinstance(built, WizardPattern)
    return built
