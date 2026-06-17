"""CLI package tests — dispatch and EmbeddedRuntime integration."""

from __future__ import annotations

import json

import pytest

from palm.app.cli_settings import resolve_cli_settings
from palm.runtimes.cli.commands.registry import build_registry
from palm.runtimes.cli.shared.args import CliInvocation, settings_from_invocation
from palm.runtimes.cli.shared.bootstrap import bootstrap_runtime, shutdown_context
from tests.fast_settings import make_test_settings
from palm.runtimes.cli.shared.instance_ops import (
    filter_summaries,
    is_terminal_status,
    parse_instance_list_flags,
)


def test_process_list_registers_examples(cli_ctx) -> None:
    reg = build_registry()
    assert reg.dispatch(cli_ctx, "process list") == 0
    names = {p.name for p in cli_ctx.app.list_processes()}
    assert "onboarding" in names
    assert "quick-demo" in names
    assert "data-ingestion" in names
    assert "approval-workflow" in names


def test_resource_list_registers_example(cli_ctx) -> None:
    reg = build_registry()
    assert reg.dispatch(cli_ctx, "resource list") == 0
    names = {item.name for item in cli_ctx.app.list_resources()}
    assert "fetch-customer" in names


def test_resource_describe_example(cli_ctx) -> None:
    reg = build_registry()
    assert reg.dispatch(cli_ctx, "resource describe fetch-customer") == 0


def test_resource_invoke_example(cli_ctx) -> None:
    reg = build_registry()
    assert reg.dispatch(cli_ctx, "resource invoke fetch-customer customer_id=cust-42") == 0


def test_doctor_reports_healthy(cli_ctx) -> None:
    reg = build_registry()
    assert reg.dispatch(cli_ctx, "doctor") == 0


def test_wizard_start_onboard(cli_ctx) -> None:
    reg = build_registry()
    assert reg.dispatch(cli_ctx, "wizard start onboard") == 0
    assert cli_ctx.active_instance_id is not None


def test_flow_start_onboard(cli_ctx) -> None:
    reg = build_registry()
    assert reg.dispatch(cli_ctx, "flow start onboard") == 0
    assert cli_ctx.active_instance_id is not None


def test_start_alias_schema_onboard(cli_ctx) -> None:
    reg = build_registry()
    assert reg.dispatch(cli_ctx, "start schema-onboard") == 0
    assert cli_ctx.active_instance_id is not None


def test_flow_start_todo_builder(cli_ctx) -> None:
    import shlex

    from palm.runtimes.cli.shared.job_inspect import inspect_job

    reg = build_registry()
    assert reg.dispatch(cli_ctx, "flow start todo-builder") == 0
    iid = cli_ctx.active_instance_id
    assert iid is not None

    steps = [
        "yes",
        "Add a new item",
        "Buy milk",
        "",
        "high",
        "Add a new item",
        "Walk dog",
        "",
        "medium",
        "Continue to summary",
        "yes",
        "yes",
    ]
    for value in steps:
        cmd = "input " + shlex.quote(value)
        assert reg.dispatch(cli_ctx, cmd) == 0, cmd
        job = inspect_job(cli_ctx.job_for_instance(iid))
        assert job.validation_error is None, f"failed on input {value!r}: {job.validation_error}"

    job = inspect_job(cli_ctx.job_for_instance(iid))
    assert job.pattern == "wizard"
    assert job.answers_preview.get("todos") == [
        {"title": "Buy milk", "priority": "high"},
        {"title": "Walk dog", "priority": "medium"},
    ]


def test_flow_start_parallel_demo(cli_ctx) -> None:
    from palm.runtimes.cli.shared.job_inspect import inspect_job

    reg = build_registry()
    assert reg.dispatch(cli_ctx, "flow start parallel-demo") == 0
    iid = cli_ctx.active_instance_id
    assert iid is not None
    job = cli_ctx.job_for_instance(iid)
    assert inspect_job(job).pattern == "parallel"


def test_flow_list_includes_parallel(cli_ctx) -> None:
    reg = build_registry()
    assert reg.dispatch(cli_ctx, "flow list") == 0
    names = {flow.name for flow in cli_ctx.app.list_flows()}
    assert "parallel-demo" in names
    assert "schema-onboard" in names


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
    monkeypatch.delenv("PALM_DATA_DIR", raising=False)
    monkeypatch.setenv("PALM_STORAGE_BACKEND", "filesystem")
    monkeypatch.setenv("PALM_DATA_DIR", "/tmp/palm-cli-data")
    monkeypatch.setenv("PALM_ENABLE_STATE_SNAPSHOT", "true")

    cfg = resolve_cli_settings()
    assert cfg.storage_backend == "filesystem"
    assert str(cfg.data_dir) == "/tmp/palm-cli-data"
    assert cfg.enable_state_snapshot is True

    overridden = resolve_cli_settings(storage_backend="memory")
    assert overridden.storage_backend == "memory"


@pytest.mark.slow
def test_cli_filesystem_persistence_across_sessions(tmp_path) -> None:
    reg = build_registry()

    fs_settings = make_test_settings(
        load_examples=True,
        storage_backend="filesystem",
        data_dir=tmp_path,
    )
    ctx1 = bootstrap_runtime(settings=fs_settings, show_banner=False)
    try:
        assert ctx1.app.settings.storage_backend == "filesystem"
        assert ctx1.instance_manager.is_initialized
        reg.dispatch(ctx1, "wizard start quick")
        iid = ctx1.active_instance_id
        assert iid is not None
        reg.dispatch(ctx1, f"input {iid} first")
    finally:
        shutdown_context(ctx1)

    ctx2 = bootstrap_runtime(settings=fs_settings, show_banner=False)
    try:
        summaries = ctx2.list_instance_summaries()
        assert any(item.instance_id == iid for item in summaries)
        assert reg.dispatch(ctx2, f"process resume {iid}") == 0
        assert ctx2.active_instance_id == iid
        job_id = ctx2.resolve_job_id(iid)
        assert ctx2.app.current_wizard_step(job_id) == "beta"
    finally:
        shutdown_context(ctx2)


@pytest.mark.slow
def test_cli_env_settings_used_when_flags_omitted(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("PALM_DATA_DIR", raising=False)
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


@pytest.mark.slow
def test_instance_list_to_status_filesystem(tmp_path) -> None:
    reg = build_registry()

    fs_settings = make_test_settings(
        load_examples=True,
        storage_backend="filesystem",
        data_dir=tmp_path,
    )
    ctx1 = bootstrap_runtime(settings=fs_settings, show_banner=False)
    try:
        reg.dispatch(ctx1, "wizard start quick")
        iid = ctx1.active_instance_id
        assert iid is not None
        reg.dispatch(ctx1, f"input {iid} first")
    finally:
        shutdown_context(ctx1)

    ctx2 = bootstrap_runtime(settings=fs_settings, show_banner=False)
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

    ctx3 = bootstrap_runtime(settings=fs_settings, show_banner=False)
    try:
        assert reg.dispatch(ctx3, f"process resume {listed_id[:14]}") == 0
    finally:
        shutdown_context(ctx3)


def test_shared_storage_aligns_settings() -> None:
    import palm.storages.memory  # noqa: F401
    from palm.core import StorageEngine

    storage = StorageEngine()
    storage.initialize(backend="memory")
    ctx = bootstrap_runtime(
        storage=storage,
        settings=make_test_settings(load_examples=True),
        show_banner=False,
    )
    try:
        assert ctx.app.settings.storage_backend == "memory"
        assert ctx.app.storage.backend_name == "memory"
        assert ctx.app.instance_manager is ctx.instance_manager
    finally:
        shutdown_context(ctx)
        storage.shutdown()


def test_status_defaults_to_active_instance(cli_ctx) -> None:
    reg = build_registry()
    reg.dispatch(cli_ctx, "wizard start quick")
    iid = cli_ctx.active_instance_id
    assert iid is not None
    assert reg.dispatch(cli_ctx, "status") == 0
    assert reg.dispatch(cli_ctx, "instance status") == 0


def test_instance_list_json_format(cli_ctx) -> None:
    from io import StringIO

    from rich.console import Console

    reg = build_registry()
    reg.dispatch(cli_ctx, "wizard start quick")
    cli_ctx.output_format = "json"

    buf = StringIO()
    cli_ctx.console = Console(file=buf, force_terminal=False, width=120)
    assert reg.dispatch(cli_ctx, "instance list") == 0
    payload = json.loads(buf.getvalue())
    assert isinstance(payload, list)
    assert len(payload) >= 1
    assert "instance_id" in payload[0]
    assert "short_id" in payload[0]


def test_instance_list_active_vs_all(cli_ctx) -> None:
    reg = build_registry()
    reg.dispatch(cli_ctx, "wizard start quick")
    summaries = cli_ctx.list_instance_summaries()
    active = [s for s in summaries if not is_terminal_status(s.status)]
    assert len(active) >= 1

    options_active, _ = parse_instance_list_flags([])
    filtered = filter_summaries(summaries, options=options_active)
    assert all(not is_terminal_status(s.status) for s in filtered)

    options_all, _ = parse_instance_list_flags(["--all"])
    filtered_all = filter_summaries(summaries, options=options_all)
    assert len(filtered_all) >= len(filtered)


def test_instance_prune_dry_run(cli_ctx) -> None:
    reg = build_registry()
    cli_ctx.output_format = "json"
    assert reg.dispatch(cli_ctx, "instance prune --dry-run") == 0


def test_cli_flags_override_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PALM_STORAGE_BACKEND", "filesystem")
    monkeypatch.setenv("PALM_MAX_LOADED_INSTANCES", "99")

    inv = CliInvocation(
        command="repl",
        storage_backend="memory",
        max_loaded_instances=5,
    )
    cfg = settings_from_invocation(inv)
    assert cfg.storage_backend == "memory"
    assert cfg.max_loaded_instances == 5


def test_repl_completer_builds(cli_ctx) -> None:
    from prompt_toolkit.completion import Completer, Completion

    from palm.runtimes.cli.tui.completion import build_repl_completer

    reg = build_registry()
    completer = build_repl_completer(
        cli_ctx, reg, completer_cls=Completer, completion_cls=Completion
    )
    assert completer is not None


@pytest.mark.slow
def test_process_resume() -> None:
    import palm.storages.memory  # noqa: F401
    from palm.core import StorageEngine

    storage = StorageEngine()
    storage.initialize(backend="memory")
    reg = build_registry()

    resume_settings = make_test_settings(load_examples=True)
    ctx1 = bootstrap_runtime(storage=storage, settings=resume_settings, show_banner=False)
    try:
        reg.dispatch(ctx1, "wizard start quick")
        iid = ctx1.active_instance_id
        assert iid is not None
        reg.dispatch(ctx1, f"input {iid} first")
    finally:
        shutdown_context(ctx1)

    ctx2 = bootstrap_runtime(storage=storage, settings=resume_settings, show_banner=False)
    try:
        assert reg.dispatch(ctx2, f"process resume {iid}") == 0
        assert ctx2.active_instance_id == iid
        job_id = ctx2.resolve_job_id(iid)
        assert ctx2.app.current_wizard_step(job_id) == "beta"
    finally:
        shutdown_context(ctx2)
        storage.shutdown()
