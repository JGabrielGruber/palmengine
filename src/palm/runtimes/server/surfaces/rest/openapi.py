"""Minimal OpenAPI 3.0 document for the REST surface."""

from __future__ import annotations

from typing import Any


def build_openapi_spec(*, version: str) -> dict[str, Any]:
    """Return a machine-readable API description for tooling and clients."""
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "Palm Engine API",
            "version": version,
            "description": "Registry-driven REST surface for Palm orchestration.",
        },
        "paths": {
            "/health": {
                "get": {
                    "summary": "Health check",
                    "responses": {"200": {"description": "Server is healthy"}},
                }
            },
            "/v1/jobs": {
                "get": {
                    "summary": "List jobs",
                    "parameters": [
                        {"name": "status", "in": "query", "schema": {"type": "string"}},
                        {"name": "limit", "in": "query", "schema": {"type": "integer", "default": 50}},
                        {"name": "offset", "in": "query", "schema": {"type": "integer", "default": 0}},
                    ],
                    "responses": {"200": {"description": "Paginated job list"}},
                },
                "post": {
                    "summary": "Submit a flow job",
                    "responses": {"202": {"description": "Job accepted"}},
                },
            },
            "/v1/jobs/{job_id}": {
                "get": {
                    "summary": "Get job status",
                    "parameters": [
                        {"name": "job_id", "in": "path", "required": True, "schema": {"type": "string"}},
                    ],
                    "responses": {"200": {"description": "Job details"}},
                },
            },
            "/v1/jobs/{job_id}/input": {
                "post": {
                    "summary": "Provide interactive input",
                    "responses": {"200": {"description": "Input accepted"}},
                },
            },
            "/v1/plans/prepare": {
                "post": {
                    "summary": "Stage execution plans",
                    "responses": {"201": {"description": "Plans staged"}},
                },
            },
            "/v1/plans/submit": {
                "post": {
                    "summary": "Submit staged plans",
                    "responses": {"202": {"description": "Jobs accepted"}},
                },
            },
            "/v1/instances": {
                "get": {
                    "summary": "List process instances",
                    "parameters": [
                        {"name": "status", "in": "query", "schema": {"type": "string"}},
                        {"name": "flow_name", "in": "query", "schema": {"type": "string"}},
                        {"name": "include_terminal", "in": "query", "schema": {"type": "boolean"}},
                        {"name": "limit", "in": "query", "schema": {"type": "integer"}},
                        {"name": "offset", "in": "query", "schema": {"type": "integer"}},
                    ],
                    "responses": {"200": {"description": "Paginated instance list"}},
                },
            },
            "/v1/instances/{instance_id}": {
                "get": {
                    "summary": "Get instance status",
                    "parameters": [
                        {
                            "name": "instance_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        },
                    ],
                    "responses": {"200": {"description": "Instance details"}},
                },
            },
            "/v1/instances/{instance_id}/resume": {
                "post": {
                    "summary": "Resume a persisted instance",
                    "responses": {"202": {"description": "Resume accepted"}},
                },
            },
        },
        "components": {
            "schemas": {
                "Error": {
                    "type": "object",
                    "properties": {
                        "error": {"type": "string"},
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
                    "required": ["error", "message"],
                },
                "Pagination": {
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer"},
                        "offset": {"type": "integer"},
                        "count": {"type": "integer"},
                        "total": {"type": "integer"},
                        "has_more": {"type": "boolean"},
                    },
                },
            },
        },
    }