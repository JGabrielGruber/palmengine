"""Unit tests for assist REST route table."""

from __future__ import annotations

from bundles.standard.runtimes.server.surfaces.rest.assist.routes import ROUTES


def test_assist_routes_include_start_and_handoff() -> None:
    paths = {(entry.method, entry.path) for entry in ROUTES}
    assert ("POST", "/v1/api/assist/scenarios/{scenario_id}/start") in paths
    assert ("POST", "/v1/api/assist/instance/{instance_id}/handoff") in paths
    assert ("GET", "/v1/api/assist/scenarios") in paths
    assert ("GET", "/v1/api/assist/doctor") in paths
    assert ("GET", "/v1/api/assist/catalog/flows") in paths