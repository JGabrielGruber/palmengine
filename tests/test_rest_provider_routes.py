"""Unit tests for provider invoke REST route table."""

from __future__ import annotations

from palm.runtimes.server.surfaces.rest.execution.providers.routes import ROUTES


def test_provider_routes_use_service_path_shape() -> None:
    paths = {route.path for route in ROUTES}
    assert "/v1/api/providers/{provider}/{resource_ref}/invoke" in paths
    assert "/v1/api/resources/{resource_ref}/invoke" in paths
    assert "/v1/resources/invoke" not in paths