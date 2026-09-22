"""Unit tests for flow command-path REST route table."""

from __future__ import annotations

from bundles.standard.runtimes.server.surfaces.rest.execution.flows.routes import ROUTES


def test_flow_routes_use_command_path_shape() -> None:
    paths = {route.path for route in ROUTES}
    assert "/v1/api/flows" in paths
    assert "/v1/api/flows/{flow_id}" in paths
    assert "/v1/api/flows/{flow_id}/create" in paths
    assert "/v1/api/flows/{flow_id}/instance/{instance_id}" in paths
    assert "/v1/api/flows/{flow_id}/instance/{instance_id}/input" in paths
    assert "/v1/api/flows/{flow_id}/instances" not in paths
    assert "/v1/api/flows/instances/{instance_id}" not in paths