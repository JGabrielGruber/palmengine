"""Hermetic job contract + dogfood definitions (0.54.1-0.54.2)."""

from __future__ import annotations

import pytest

from plugins.runners.neonroot.contract import (
    HERMETIC_JOB_SPAWN_FIELDS,
    hermetic_job_summary,
    validate_hermetic_job_params,
)


def test_validate_requires_image_and_command() -> None:
    with pytest.raises(ValueError, match="image"):
        validate_hermetic_job_params({"command": ["true"]})
    with pytest.raises(ValueError, match="command"):
        validate_hermetic_job_params({"image": "palm-ci"})


def test_validate_spawn_contract_shape() -> None:
    req = validate_hermetic_job_params(
        {
            "image": "palm-ci",
            "command": ["true"],
            "seed": "git-archive",
            "seed_exclude": ["data/", ".venv/"],
            "outputs": [{"host": "/tmp/out.txt", "container": "out.txt"}],
            "vault": "palm-ci",
            "sandbox": True,
        }
    )
    assert req.image == "palm-ci"
    assert req.command == ("true",)
    assert req.seed == "git-archive"
    assert "data/" in req.seed_exclude
    assert any(o.endswith("out.txt") for o in req.outputs)

    summary = hermetic_job_summary(req)
    assert summary["kind"] == "hermetic_job"
    assert summary["runtime"] == "neonroot"
    assert set(summary["command"]) == {"true"}


def test_known_fields_documented() -> None:
    assert "image" in HERMETIC_JOB_SPAWN_FIELDS
    assert "command" in HERMETIC_JOB_SPAWN_FIELDS
    assert "outputs" in HERMETIC_JOB_SPAWN_FIELDS
    assert "seed_mode" in HERMETIC_JOB_SPAWN_FIELDS


def test_seed_mode_bind_requires_host_path() -> None:
    with pytest.raises(ValueError, match="bind"):
        validate_hermetic_job_params(
            {
                "image": "palm-ci",
                "command": ["true"],
                "seed": "git-archive",
                "seed_mode": "bind",
            }
        )
    with pytest.raises(ValueError, match="seed_exclude"):
        validate_hermetic_job_params(
            {
                "image": "palm-ci",
                "command": ["true"],
                "seed": "/tmp/ws",
                "seed_mode": "bind",
                "seed_exclude": ["data/"],
            }
        )
    req = validate_hermetic_job_params(
        {
            "image": "palm-docs",
            "command": ["true"],
            "seed": "/tmp/docs",
            "seed_mode": "bind",
        }
    )
    assert req.seed_mode == "bind"


def test_hermetic_job_smoke_definitions() -> None:
    from examples.definitions.hermetic_job_smoke import (
        HERMETIC_JOB_SMOKE_FLOW,
        register_definitions,
    )

    steps = HERMETIC_JOB_SMOKE_FLOW.options["steps"]
    run = next(s for s in steps if s["slug"] == "run_true")
    assert run["step_kind"] == "workload"
    assert run["params"]["placement"]["runtime"] == "neonroot"
    assert run["params"]["image"] == "palm-ci"

    class _Repo:
        def __init__(self) -> None:
            self.n = 0

        def save_flow(self, _f):
            self.n += 1

        def save_process(self, _p):
            self.n += 1

    repo = _Repo()
    register_definitions(repo)
    # 3 flows + 3 processes (smoke + dag + fanout)
    assert repo.n == 6


def test_hermetic_ci_slice_definitions() -> None:
    """CI slice uses neonroot WorkloadRuntime via DAG workload nodes."""
    from examples.definitions.hermetic_ci_slice import (
        HERMETIC_CI_SLICE_FLOW,
        register_definitions,
    )

    nodes = {n["id"]: n for n in HERMETIC_CI_SLICE_FLOW.options["nodes"]}
    assert "workload" in nodes["ruff"]
    assert nodes["guard_core"]["depends_on"] == ["ruff"]
    assert nodes["ruff"]["workload"]["placement"]["runtime"] == "neonroot"
    assert HERMETIC_CI_SLICE_FLOW.pattern == "dag"

    class _Repo:
        def __init__(self) -> None:
            self.n = 0

        def save_flow(self, _f):
            self.n += 1

        def save_process(self, _p):
            self.n += 1

    repo = _Repo()
    register_definitions(repo)
    assert repo.n == 2
