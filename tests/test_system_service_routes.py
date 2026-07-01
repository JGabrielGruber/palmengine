"""Tests for system service REST route registration."""

from __future__ import annotations

from palm.runtimes.server.surfaces.rest.system.routes import ROUTES


def test_system_routes_include_job_context_and_instances() -> None:
    paths = {(entry.method, entry.path) for entry in ROUTES}
    assert ("GET", "/v1/api/system/jobs/{job_id}/context") in paths
    assert ("POST", "/v1/api/system/jobs/{job_id}/cancel") in paths
    assert ("GET", "/v1/api/system/instances") in paths
    assert ("GET", "/v1/api/system/instances/{instance_id}/tree") in paths
    assert ("GET", "/v1/api/system/instances/{instance_id}/snapshots") in paths
    assert ("GET", "/v1/api/system/instances/{instance_id}/snapshots/{snapshot_id}") in paths
    assert ("POST", "/v1/api/system/instances/{instance_id}/resume") in paths