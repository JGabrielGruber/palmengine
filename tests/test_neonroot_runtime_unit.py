"""NeonRoot as WorkloadRuntime only (provider removed 0.56)."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from palm.core.registry import provider_registry
from palm.core.workload import (
    IsolationPolicy,
    LifecyclePolicy,
    WorkloadEngine,
    WorkloadKind,
    WorkloadPlacement,
    WorkloadSpec,
    WorkloadStatus,
)
from palm.core.workload.registry import workload_runtime_registry
from plugins.runners.neonroot.cli import NeonrootProbe
from plugins.runners.neonroot.runtime import NeonrootWorkloadRuntime
from plugins.runners.neonroot.spawn import (
    SpawnRequest,
    build_spawn_argv,
    parse_spawn_params,
)


def test_neonroot_not_in_provider_registry() -> None:
    import plugins.providers  # noqa: F401
    import plugins.runners  # noqa: F401

    assert "neonroot" not in provider_registry.names()
    assert "neonroot" in workload_runtime_registry.names()


def test_parse_and_build_spawn_argv() -> None:
    req = parse_spawn_params(
        {"image": "palm-ci", "command": ["true"], "seed": "none", "sandbox": True}
    )
    assert isinstance(req, SpawnRequest)
    argv = build_spawn_argv("/usr/bin/neonroot", req, seed_path=None)
    assert argv[:2] == ["/usr/bin/neonroot", "spawn"]
    assert "--image" in argv
    assert "palm-ci" in argv
    assert argv[-1] == "true"


def test_engine_start_via_neonroot_runtime_mock() -> None:
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
        patch("plugins.runners.neonroot.spawn.run_spawn", return_value=payload),
        patch("plugins.runners.neonroot.spawn.resolve_repo_root", return_value=None),
    ):
        wl = engine.start(
            WorkloadSpec(
                kind=WorkloadKind.RUN,
                isolation=IsolationPolicy.HERMETIC,
                lifecycle=LifecyclePolicy.JOB,
                image="palm-ci",
                command=("true",),
                seed={"type": "none"},
                placement=WorkloadPlacement(runtime="neonroot"),
            )
        )
    assert wl.status is WorkloadStatus.STOPPED
    assert wl.result is not None and wl.result.success
    engine.shutdown()


def test_hermetic_contract_validate() -> None:
    from plugins.runners.neonroot.contract import validate_hermetic_job_params

    req = validate_hermetic_job_params({"image": "palm-ci", "command": ["true"]})
    assert req.image == "palm-ci"
    with pytest.raises(ValueError):
        validate_hermetic_job_params({"command": ["true"]})
