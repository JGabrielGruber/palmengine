"""Unit tests for definitions CRUD REST route table."""

from __future__ import annotations

from palm.runtimes.server.surfaces.rest.definitions.routes import ROUTES


def test_definitions_routes_include_crud_verbs() -> None:
    keys = {(route.method, route.path) for route in ROUTES}
    assert ("POST", "/v1/api/definitions/flows") in keys
    assert ("PUT", "/v1/api/definitions/flows/{flow_id}") in keys
    assert ("DELETE", "/v1/api/definitions/flows/{flow_id}") in keys
    assert ("POST", "/v1/api/definitions/resources") in keys
    assert ("DELETE", "/v1/api/definitions/resources/{resource_ref}") in keys


def test_definitions_routes_include_revision_verbs() -> None:
    keys = {(route.method, route.path) for route in ROUTES}
    assert ("GET", "/v1/api/definitions/flows/{flow_id}/impact") in keys
    assert ("POST", "/v1/api/definitions/instances/{instance_id}/migrate") in keys