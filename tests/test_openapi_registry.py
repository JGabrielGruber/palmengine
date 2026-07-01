"""Tests for OpenAPI route aggregation from per-service registries."""

from __future__ import annotations

from palm import __version__
from palm.runtimes.server.surfaces.rest.openapi import build_openapi_spec
from palm.runtimes.server.surfaces.rest.openapi_registry import (
    collect_service_routes,
    meta_routes,
    rest_routes,
)
from palm.runtimes.server.surfaces.rest.route_table import rest_routes as table_rest_routes


def test_collect_service_routes_includes_system_and_flows() -> None:
    paths = {(route.method, route.path) for route in collect_service_routes()}
    assert ("GET", "/v1/api/system/jobs/{job_id}/context") in paths
    assert ("POST", "/v1/api/flows/{flow_id}/create") in paths
    assert ("POST", "/v1/api/processes/{process_id}/prepare") in paths
    assert ("POST", "/v1/api/assist/scenarios/{scenario_id}/start") in paths


def test_rest_routes_merges_meta_and_service() -> None:
    assert len(rest_routes()) == len(meta_routes()) + len(collect_service_routes())
    assert table_rest_routes() == rest_routes()


def test_openapi_includes_flows_create_and_system_context() -> None:
    doc = build_openapi_spec(version=__version__)
    paths = doc["paths"]
    assert "/v1/api/flows/{flow_id}/create" in paths
    assert "/v1/api/system/jobs/{job_id}/context" in paths
    assert "post" in paths["/v1/api/flows/{flow_id}/create"]
    assert paths["/v1/api/flows/{flow_id}/create"]["post"]["security"] == [{"PalmSubject": []}]


def test_openapi_tags_cover_service_domains() -> None:
    doc = build_openapi_spec(version=__version__)
    tag_names = {tag["name"] for tag in doc["tags"]}
    assert {"Meta", "Assist", "System", "Flows", "Definitions", "Processes", "Providers"} <= tag_names