"""Neonroot WorkloadRuntime — Spec→SpawnRequest→CLI (Spec-native)."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from palm.core.workload import (
    IsolationPolicy,
    LifecyclePolicy,
    WorkloadEngine,
    WorkloadKind,
    WorkloadPlacement,
    WorkloadSpec,
    WorkloadStatus,
)
from plugins.runners.neonroot.cli import NeonrootProbe
from plugins.runners.neonroot.runtime import NeonrootWorkloadRuntime
from plugins.runners.neonroot.spec_map import spawn_request_from_spec


def _hermetic_run(*, image: str = "palm-ci", seed: dict | None = None) -> WorkloadSpec:
    return WorkloadSpec(
        kind=WorkloadKind.RUN,
        isolation=IsolationPolicy.HERMETIC,
        lifecycle=LifecyclePolicy.JOB,
        image=image,
        command=("true",),
        placement=WorkloadPlacement(runtime="neonroot"),
        seed=seed if seed is not None else {"type": "none"},
    )


def test_spawn_request_from_spec_seed_none() -> None:
    req = spawn_request_from_spec(_hermetic_run())
    assert req.image == "palm-ci"
    assert req.command == ("true",)
    assert req.seed == "none"
    assert req.isolated is True
    assert req.sandbox is True


def test_spawn_request_default_seed_hermetic_is_git_archive() -> None:
    spec = WorkloadSpec(
        kind=WorkloadKind.RUN,
        isolation=IsolationPolicy.HERMETIC,
        lifecycle=LifecyclePolicy.JOB,
        image="palm-ci",
        command=("true",),
        placement=WorkloadPlacement(runtime="neonroot"),
        seed=None,
    )
    req = spawn_request_from_spec(spec)
    assert req.seed == "git-archive"


def test_spawn_request_path_and_outputs() -> None:
    spec = WorkloadSpec(
        kind=WorkloadKind.RUN,
        isolation=IsolationPolicy.HERMETIC,
        lifecycle=LifecyclePolicy.JOB,
        image="palm-ci",
        command=("ruff", "check"),
        seed={"type": "path", "path": "docs/", "exclude": [".venv/"]},
        resources={
            "outputs": [{"host": "out/a.css", "container": "a.css"}],
            "vault": "palm-ci",
        },
        labels={"name": "docs-job"},
        placement=WorkloadPlacement(runtime="neonroot"),
        timeout_s=90,
    )
    req = spawn_request_from_spec(spec)
    assert req.seed == "docs/"
    assert req.seed_mode == "copy"
    assert ".venv/" in req.seed_exclude
    assert req.vault == "palm-ci"
    assert req.name == "docs-job"
    assert req.timeout == 90.0
    assert any("a.css" in o for o in req.outputs)


def test_spawn_request_bind_rejects_exclude() -> None:
    with pytest.raises(ValueError, match="bind"):
        spawn_request_from_spec(
            WorkloadSpec(
                kind=WorkloadKind.RUN,
                isolation=IsolationPolicy.BEST_EFFORT,
                lifecycle=LifecyclePolicy.JOB,
                image="palm-ci",
                command=("true",),
                seed={"type": "bind", "path": "/tmp/ws", "exclude": ["x"]},
                placement=WorkloadPlacement(runtime="neonroot"),
            )
        )


def test_neonroot_missing_cli_fails_closed() -> None:
    rt = NeonrootWorkloadRuntime()
    engine = WorkloadEngine()
    engine.initialize(runtimes={"neonroot": rt})
    missing = NeonrootProbe(available=False, error="neonroot not found on PATH")
    with patch("plugins.runners.neonroot.cli.probe_neonroot", return_value=missing):
        wl = engine.start(_hermetic_run())
    assert wl.status is WorkloadStatus.FAILED
    assert wl.result is not None
    assert (wl.result.runtime_meta or {}).get("error_class") == "runtime_unavailable" or (
        "neonroot" in (wl.result.error or "").lower()
    )
    engine.shutdown()


def test_neonroot_spawn_success_mapped() -> None:
    rt = NeonrootWorkloadRuntime()
    engine = WorkloadEngine()
    engine.initialize(runtimes={"neonroot": rt})
    present = NeonrootProbe(available=True, path="/bin/neonroot", version="0.2")
    payload = {
        "exit_code": 0,
        "stdout_tail": "ok",
        "stderr_tail": "",
        "duration_s": 0.1,
        "image": "palm-ci",
        "neonroot": present.as_dict(),
    }
    with (
        patch("plugins.runners.neonroot.cli.probe_neonroot", return_value=present),
        patch("plugins.runners.neonroot.spawn.run_spawn_request", return_value=payload),
        patch("plugins.runners.neonroot.spawn.resolve_repo_root", return_value=None),
    ):
        wl = engine.start(_hermetic_run())
    assert wl.status is WorkloadStatus.STOPPED
    assert wl.result is not None and wl.result.success
    engine.shutdown()


def test_neonroot_rejects_workspace_kind() -> None:
    rt = NeonrootWorkloadRuntime()
    engine = WorkloadEngine()
    engine.initialize(runtimes={"neonroot": rt})
    wl = engine.start(
        WorkloadSpec(
            kind=WorkloadKind.WORKSPACE,
            isolation=IsolationPolicy.HERMETIC,
            lifecycle=LifecyclePolicy.SESSION,
            image="palm-ci",
            placement=WorkloadPlacement(runtime="neonroot"),
        )
    )
    assert wl.status is WorkloadStatus.FAILED
    text = f"{wl.message or ''} {(wl.result.error if wl.result else '')}".lower()
    assert "workspace" in text or "kind=run" in text
    engine.shutdown()


def test_neonroot_health_and_doctor_shape() -> None:
    import plugins.runners  # noqa: F401
    from palm.core.workload.registry import workload_runtime_registry

    assert "neonroot" in workload_runtime_registry.names()
    present = NeonrootProbe(available=True, path="/bin/neonroot", version="0.2")
    with patch("plugins.runners.neonroot.cli.probe_neonroot", return_value=present):
        h = NeonrootWorkloadRuntime().health()
        assert h.available is True
        assert h.to_dict()["detail"]["path"] == "/bin/neonroot"
