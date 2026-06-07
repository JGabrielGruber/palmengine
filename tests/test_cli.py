"""CLI package tests — dispatch and EmbeddedRuntime integration."""

from __future__ import annotations

import pytest

from palm.runtimes.cli_pkg.bootstrap import bootstrap_runtime, shutdown_context
from palm.runtimes.cli_pkg.commands.registry import build_registry


@pytest.fixture
def cli_ctx():
    ctx = bootstrap_runtime()
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


def test_process_resume() -> None:
    import palm.storages.memory  # noqa: F401
    from palm.core import StorageEngine

    storage = StorageEngine()
    storage.initialize(backend="memory")
    reg = build_registry()

    ctx1 = bootstrap_runtime(storage=storage)
    try:
        reg.dispatch(ctx1, "wizard start quick")
        iid = ctx1.active_instance_id
        assert iid is not None
        reg.dispatch(ctx1, f"input {iid} first")
    finally:
        shutdown_context(ctx1)

    ctx2 = bootstrap_runtime(storage=storage)
    try:
        assert reg.dispatch(ctx2, f"process resume {iid}") == 0
        assert ctx2.active_instance_id == iid
        job_id = ctx2.resolve_job_id(iid)
        assert ctx2.app.current_wizard_step(job_id) == "beta"
    finally:
        shutdown_context(ctx2)
        storage.shutdown()
