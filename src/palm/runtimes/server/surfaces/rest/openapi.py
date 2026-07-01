"""OpenAPI 3.0 generation from the central REST route table."""

from __future__ import annotations

from typing import Any

from palm.runtimes.server.surfaces.rest.doc_examples import (
    GROUP_DESCRIPTIONS,
    OPENAPI_REQUEST_EXAMPLES,
)
from palm.runtimes.server.surfaces.rest.route_table import RouteDefinition, rest_routes
from palm.runtimes.server.surfaces.rest.schemas import openapi_components

_ERROR_REF = {"$ref": "#/components/schemas/Error"}
_JSON_BODY = "application/json"


def build_openapi_spec(*, version: str) -> dict[str, Any]:
    """Build an OpenAPI document from :func:`rest_routes` and shared schemas."""
    paths: dict[str, Any] = {}
    tags: dict[str, dict[str, str]] = {}

    for route in rest_routes():
        _ensure_tag(tags, route.group)
        path_item = paths.setdefault(route.path, {})
        operation = _operation(route)
        path_item[route.method.lower()] = operation

    return {
        "openapi": "3.0.3",
        "info": {
            "title": "Palm Engine API",
            "version": version,
            "description": (
                "Service-domain REST surface for Palm orchestration. "
                "Flows sessions, process execution, system observe/lifecycle, "
                "definition catalog, and provider invocation under /v1/api/…."
            ),
        },
        "tags": [
            {"name": name, "description": meta["description"]}
            for name, meta in sorted(tags.items())
        ],
        "paths": paths,
        "components": {
            "schemas": {
                **openapi_components(),
                "Error": _error_schema(),
                "Pagination": _pagination_schema(),
            },
            "securitySchemes": {
                "PalmSubject": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-Palm-Subject",
                    "description": "Principal subject when auth enforcement is enabled.",
                },
            },
        },
    }


def _operation(route: RouteDefinition) -> dict[str, Any]:
    operation: dict[str, Any] = {
        "tags": [route.group],
        "summary": route.summary,
        "description": route.description,
        "responses": _responses(route),
    }
    if route.auth_required:
        operation["security"] = [{"PalmSubject": []}]
    if route.request_schema:
        operation["requestBody"] = {
            "required": True,
            "content": {
                _JSON_BODY: {
                    "schema": {"$ref": f"#/components/schemas/{route.request_schema}"},
                    "examples": _request_examples(route.request_schema),
                },
            },
        }
    if route.query_schema:
        operation["parameters"] = _query_parameters(route)
    if "{" in route.path:
        operation["parameters"] = [
            *operation.get("parameters", []),
            *_path_parameters(route.path),
        ]
    return operation


def _responses(route: RouteDefinition) -> dict[str, Any]:
    success = str(route.response_status)
    responses: dict[str, Any] = {
        success: {"description": route.summary},
        "400": {"description": "Validation error", "content": {_JSON_BODY: {"schema": _ERROR_REF}}},
        "401": {"description": "Unauthorized", "content": {_JSON_BODY: {"schema": _ERROR_REF}}},
        "404": {"description": "Not found", "content": {_JSON_BODY: {"schema": _ERROR_REF}}},
    }
    return responses


def _query_parameters(route: RouteDefinition) -> list[dict[str, Any]]:
    return [
        {
            "name": "limit",
            "in": "query",
            "schema": {"type": "integer", "default": 50, "minimum": 1, "maximum": 200},
        },
        {
            "name": "offset",
            "in": "query",
            "schema": {"type": "integer", "default": 0, "minimum": 0},
        },
    ]


def _path_parameters(path: str) -> list[dict[str, Any]]:
    params: list[dict[str, Any]] = []
    for segment in path.split("/"):
        if segment.startswith("{") and segment.endswith("}"):
            name = segment[1:-1]
            params.append(
                {
                    "name": name,
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string"},
                }
            )
    return params


def _request_examples(schema_name: str) -> dict[str, Any]:
    return OPENAPI_REQUEST_EXAMPLES.get(schema_name, {})


def _ensure_tag(tags: dict[str, dict[str, str]], group: str) -> None:
    tags.setdefault(group, {"description": GROUP_DESCRIPTIONS.get(group, group)})


def _error_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "required": ["error", "message"],
        "properties": {
            "error": {"type": "string", "example": "validation_failed"},
            "message": {"type": "string"},
            "detail": {"type": "string"},
            "details": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "field": {"type": "string"},
                        "message": {"type": "string"},
                    },
                },
            },
        },
    }


def _pagination_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "limit": {"type": "integer"},
            "offset": {"type": "integer"},
            "count": {"type": "integer"},
            "total": {"type": "integer"},
            "has_more": {"type": "boolean"},
        },
    }
