"""Studio flow templates — curated examples for one-click loading."""

from __future__ import annotations

from typing import Any

from palm.common.runtimes.server.protocol import ServerResponse

_BUILTIN_TEMPLATES: tuple[dict[str, Any], ...] = (
    {
        "id": "template:onboarding-wizard",
        "name": "Onboarding wizard",
        "description": "Collect name and email with validation — a classic human-first flow.",
        "pattern": "wizard",
        "category": "getting-started",
        "tags": ["wizard", "onboarding"],
        "flow": {
            "version": 1,
            "kind": "flow",
            "name": "onboarding-wizard",
            "pattern": "wizard",
            "id": "template-onboarding-wizard",
            "options": {
                "include_summary": True,
                "allow_backtrack": True,
                "steps": [
                    {
                        "slug": "name",
                        "title": "Your name",
                        "prompt": "What should we call you?",
                        "validation": [{"rule": "not_empty"}],
                    },
                    {
                        "slug": "email",
                        "title": "Email",
                        "prompt": "Enter your email address",
                        "validation": [{"rule": "not_empty"}],
                    },
                ],
            },
        },
    },
    {
        "id": "template:pipeline-transform",
        "name": "Transform pipeline",
        "description": "Chain rename and filter transforms in a linear pipeline.",
        "pattern": "pipeline",
        "category": "patterns",
        "tags": ["pipeline", "transform"],
        "flow": {
            "version": 1,
            "kind": "flow",
            "name": "transform-pipeline",
            "pattern": "pipeline",
            "id": "template-transform-pipeline",
            "options": {
                "steps": [
                    {
                        "name": "rename",
                        "source_key": "input",
                        "target_key": "renamed",
                        "rule": "rename_field",
                        "options": {"from": "value", "to": "payload"},
                    },
                    {
                        "name": "filter",
                        "source_key": "renamed",
                        "target_key": "filtered",
                        "rule": "filter_empty",
                        "options": {},
                    },
                ],
            },
        },
    },
    {
        "id": "template:review-flow",
        "name": "Review & confirm",
        "description": "Gather input, show a summary step, then commit — wizard with backtrack.",
        "pattern": "wizard",
        "category": "community",
        "tags": ["wizard", "summary", "backtrack"],
        "flow": {
            "version": 1,
            "kind": "flow",
            "name": "review-confirm",
            "pattern": "wizard",
            "id": "template-review-confirm",
            "options": {
                "include_summary": True,
                "allow_backtrack": True,
                "steps": [
                    {
                        "slug": "topic",
                        "title": "Topic",
                        "prompt": "What would you like to orchestrate?",
                        "validation": [{"rule": "not_empty"}],
                    },
                    {
                        "slug": "priority",
                        "title": "Priority",
                        "prompt": "How urgent is this? (low / medium / high)",
                    },
                    {
                        "slug": "notes",
                        "title": "Notes",
                        "prompt": "Any additional context?",
                    },
                ],
            },
        },
    },
)


def get_templates(request: object) -> ServerResponse:
    """Return curated Studio templates for one-click loading."""
    templates = [
        {
            "id": row["id"],
            "name": row["name"],
            "description": row["description"],
            "pattern": row["pattern"],
            "category": row["category"],
            "tags": list(row["tags"]),
        }
        for row in _BUILTIN_TEMPLATES
    ]
    categories = sorted({row["category"] for row in _BUILTIN_TEMPLATES})
    return ServerResponse(
        status=200,
        body={"templates": templates, "categories": categories},
    )


def get_template(request: object, *, template_id: str) -> ServerResponse:
    """Return a single template including its full flow definition."""
    for row in _BUILTIN_TEMPLATES:
        if row["id"] == template_id:
            return ServerResponse(
                status=200,
                body={
                    "template": {
                        "id": row["id"],
                        "name": row["name"],
                        "description": row["description"],
                        "pattern": row["pattern"],
                        "category": row["category"],
                        "tags": list(row["tags"]),
                        "flow": row["flow"],
                    }
                },
            )
    return ServerResponse(
        status=404,
        body={"error": "not_found", "message": f"Template {template_id!r} not found"},
    )
