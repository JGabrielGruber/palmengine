"""Unit tests for design service REST route table."""

from __future__ import annotations

from palm.runtimes.server.surfaces.rest.design.routes import ROUTES


def test_design_routes_include_proposal_lifecycle() -> None:
    keys = {(route.method, route.path) for route in ROUTES}
    assert ("POST", "/v1/api/design/proposals") in keys
    assert ("GET", "/v1/api/design/proposals") in keys
    assert ("GET", "/v1/api/design/proposals/{proposal_id}") in keys
    assert ("DELETE", "/v1/api/design/proposals/{proposal_id}") in keys
    assert ("POST", "/v1/api/design/proposals/{proposal_id}/validate") in keys
    assert ("GET", "/v1/api/design/proposals/{proposal_id}/impact") in keys
    assert ("POST", "/v1/api/design/proposals/{proposal_id}/commit") in keys