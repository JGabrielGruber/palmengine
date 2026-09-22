"""Hermetic job param contract — maps to WorkloadSpec / neonroot WorkloadRuntime.

Isolation jobs use **WorkloadEngine** with ``placement.runtime=neonroot``.
This module validates the spawn-param shape used by examples and CLI tooling.

Canonical spawn params
----------------------
``image`` (str, required) — NeonRoot image (e.g. ``palm-ci``).
``command`` (list[str], required) — argv inside the workspace (no shell).
``seed`` (str, default ``git-archive``) — ``git-archive`` | host path | ``none``.
``seed_exclude`` / ``outputs`` / ``seed_mode`` / ``vault`` / ``sandbox`` /
``isolated`` / ``timeout`` / ``name`` / ``cwd`` — see spawn module.

See ADR-023, ADR-024 (workload plane), VISION-0.56.
"""

from __future__ import annotations

from typing import Any

from plugins.runners.neonroot.spawn import SpawnRequest, parse_spawn_params

HERMETIC_JOB_SPAWN_FIELDS: frozenset[str] = frozenset(
    {
        "image",
        "command",
        "seed",
        "seed_exclude",
        "seed_excludes",
        "outputs",
        "output",
        "vault",
        "sandbox",
        "isolated",
        "keep",
        "timeout",
        "name",
        "cwd",
        "repo_root",
        "seed_mode",
    }
)


def validate_hermetic_job_params(params: dict[str, Any] | None) -> SpawnRequest:
    """Validate and normalize hermetic spawn params (raises ValueError)."""
    return parse_spawn_params(dict(params or {}))


def hermetic_job_summary(req: SpawnRequest) -> dict[str, Any]:
    """Stable summary dict for job state / Assist (no secrets)."""
    return {
        "kind": "hermetic_job",
        "runtime": "neonroot",
        "image": req.image,
        "command": list(req.command),
        "seed": req.seed,
        "seed_exclude": list(req.seed_exclude),
        "seed_mode": req.seed_mode,
        "outputs": list(req.outputs),
        "vault": req.vault,
        "sandbox": req.sandbox,
        "isolated": req.isolated,
        "timeout": req.timeout,
    }


__all__ = [
    "HERMETIC_JOB_SPAWN_FIELDS",
    "SpawnRequest",
    "hermetic_job_summary",
    "validate_hermetic_job_params",
]
