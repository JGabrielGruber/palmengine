"""CLI package tests — dispatch and EmbeddedRuntime integration."""

from __future__ import annotations

import pytest

from palm.runtimes.cli_pkg.bootstrap import bootstrap_runtime, shutdown_context
from palm.runtimes.cli_pkg.commands.registry import build_registry
from palm.runtimes.cli_pkg.settings import resolve_cli_settings


@pytest.fixture
def cli_ctx():
    ctx = bootstrap_runtime(show_banner=False)
    yield ctx
    shutdown_context(ctx)


def test_process_list_registers_examples(cli_ctx) -> None:
    reg = build_registry()
    assert reg.dispatch(cli_ctx, "process list") == 0
    names = {p.name for p in cli_ctx.app.list_processes()}
    assert "onboarding" in names
    assert "quick-demo" in names
    assert "data-ingestion" in names
    assert "approval-workflow" in names


def test_doctor_reports_healthy(cli_ctx) -> None:
    reg = build_registry()
    assert reg.dispatch(cli_ctx, "doctor") == 0


def test_wizard_start_onboard(cli_ctx) -> None:
    reg = build_registry()
    assert reg.dispatch(cli_ctx, "wizard start onboard") == 0
    assert cli_ctx.active_instance_id is not None


def test_wizard_input_advances(cli_ctx) -> None:
    reg = build_registry()
    reg.dispatch(cli_ctx, "wizard start quick")
    iid = cli_ctx.active_instance_id
    assert iid is not None
    assert reg.dispatch(cli_ctx, f"input {iid} hello") == 0
    assert reg.dispatch(cli_ctx, f"input {iid} world") == 0


def test_instance_list_after_submit(cli_ctx) -> None:
    reg = build_registry()
    reg.dispatch(cli_ctx, "process submit quick-demo")
    assert reg.dispatch(cli_ctx, "instance list") == 0
    instances = cli_ctx.app.list_instances()
    assert len(instances) >= 1


def test_resolve_cli_settings_respects_env_over_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PALM_STORAGE_BACKEND", "filesystem")
    monkeypatch.setenv("PALM_DATA_DIR", "/tmp/palm-cli-data")
    monkeypatch.setenv("PALM_ENABLE_STATE_SNAPSHOT", "true")

    cfg = resolve_cli_settings()
    assert cfg.storage_backend == "filesystem"
    assert str(cfg.data_dir) == "/tmp/palm-cli-data"
    assert cfg.enable_state_snapshot is True

    overridden = resolve_cli_settings(storage_backend="memory")
    assert overridden.storage_backend == "memory"


def test_cli_filesystem_persistence_across_sessions(tmp_path) -> None:
    reg = build_registry()

    ctx1 = bootstrap_runtime(
        storage_backend="filesystem",
        data_dir=tmp_path,
        show_banner=False,
    )
    try:
        assert ctx1.app.settings.storage_backend == "filesystem"
        assert ctx1.instance_manager.is_initialized
        reg.dispatch(ctx1, "wizard start quick")
        iid = ctx1.active_instance_id
        assert iid is not None
        reg.dispatch(ctx1, f"input {iid} first")
    finally:
        shutdown_context(ctx1)

    ctx2 = bootstrap_runtime(
        storage_backend="filesystem",
        data_dir=tmp_path,
        show_banner=False,
    )
    try:
        summaries = ctx2.list_instance_summaries()
        assert any(item.instance_id == iid for item in summaries)
        assert reg.dispatch(ctx2, f"process resume {iid}") == 0
        assert ctx2.active_instance_id == iid
        job_id = ctx2.resolve_job_id(iid)
        assert ctx2.app.current_wizard_step(job_id) == "beta"
    finally:
        shutdown_context(ctx2)


def test_cli_env_settings_used_when_flags_omitted(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PALM_STORAGE_BACKEND", "filesystem")
    monkeypatch.setenv("PALM_DATA_DIR", str(tmp_path))

    reg = build_registry()
    ctx = bootstrap_runtime(show_banner=False)
    try:
        assert ctx.app.settings.storage_backend == "filesystem"
        assert ctx.app.settings.data_dir == tmp_path
        reg.dispatch(ctx, "wizard start quick")
        assert ctx.active_instance_id is not None
    finally:
        shutdown_context(ctx)


def test_instance_list_status_snapshots_consistent(cli_ctx) -> None:
    reg = build_registry()
    reg.dispatch(cli_ctx, "wizard start quick")
    iid = cli_ctx.active_instance_id
    assert iid is not None

    assert reg.dispatch(cli_ctx, "instance list") == 0
    prefix = iid[:14]
    assert reg.dispatch(cli_ctx, f"status {prefix}") == 0
    assert reg.dispatch(cli_ctx, f"instance snapshots {prefix}") == 0


def test_instance_list_to_status_filesystem(tmp_path) -> None:
    reg = build_registry()

    ctx1 = bootstrap_runtime(
        storage_backend="filesystem",
        data_dir=tmp_path,
        show_banner=False,
    )
    try:
        reg.dispatch(ctx1, "wizard start quick")
        iid = ctx1.active_instance_id
        assert iid is not None
        reg.dispatch(ctx1, f"input {iid} first")
    finally:
        shutdown_context(ctx1)

    ctx2 = bootstrap_runtime(
        storage_backend="filesystem",
        data_dir=tmp_path,
        show_banner=False,
    )
    try:
        summaries = ctx2.list_instance_summaries()
        assert len(summaries) == 1
        listed_id = summaries[0].instance_id

        assert reg.dispatch(ctx2, "instance list") == 0
        assert reg.dispatch(ctx2, f"status {listed_id}") == 0
        assert reg.dispatch(ctx2, f"status {listed_id[:14]}") == 0
        assert reg.dispatch(ctx2, f"instance snapshots {listed_id}") == 0
    finally:
        shutdown_context(ctx2)

    ctx3 = bootstrap_runtime(
        storage_backend="filesystem",
        data_dir=tmp_path,
        show_banner=False,
    )
    try:
        assert reg.dispatch(ctx3, f"process resume {listed_id[:14]}") == 0
    finally:
        shutdown_context(ctx3)


def test_shared_storage_aligns_settings() -> None:
    import palm.storages.memory  # noqa: F401
    from palm.core import StorageEngine

    storage = StorageEngine()
    storage.initialize(backend="memory")
    ctx = bootstrap_runtime(storage=storage, show_banner=False)
    try:
        assert ctx.app.settings.storage_backend == "memory"
        assert ctx.app.storage.backend_name == "memory"
        assert ctx.app.instance_manager is ctx.instance_manager
    finally:
        shutdown_context(ctx)
        storage.shutdown()


def test_process_resume() -> None:
    import palm.storages.memory  # noqa: F401
    from palm.core import StorageEngine

    storage = StorageEngine()
    storage.initialize(backend="memory")
    reg = build_registry()

    ctx1 = bootstrap_runtime(storage=storage, show_banner=False)
    try:
        reg.dispatch(ctx1, "wizard start quick")
        iid = ctx1.active_instance_id
        assert iid is not None
        reg.dispatch(ctx1, f"input {iid} first")
    finally:
        shutdown_context(ctx1)

    ctx2 = bootstrap_runtime(storage=storage, show_banner=False)
    try:
        assert reg.dispatch(ctx2, f"process resume {iid}") == 0
        assert ctx2.active_instance_id == iid
        job_id = ctx2.resolve_job_id(iid)
        assert ctx2.app.current_wizard_step(job_id) == "beta"
    finally:
        shutdown_context(ctx2)
        storage.shutdown()
