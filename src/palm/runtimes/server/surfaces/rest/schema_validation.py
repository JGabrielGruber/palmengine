"""
Schema validation bridge — :class:`DictStateSchema` errors to REST field details.
"""

from __future__ import annotations

from typing import Any

from palm.common.runtimes.server.protocol import ServerRequest, ServerResponse
from palm.core.context.state_schema import DictStateSchema
from palm.runtimes.server.surfaces.rest import errors


def schema_errors_to_details(error_messages: list[str]) -> list[dict[str, str]]:
    """Convert :meth:`DictStateSchema.validate_state` messages to REST ``details``."""
    details: list[dict[str, str]] = []
    for message in error_messages:
        field, text = _split_schema_error(message)
        details.append({"field": field, "message": text})
    return details


def validate_body(
    request: ServerRequest,
    schema: DictStateSchema,
    *,
    extra_errors: list[str] | None = None,
) -> dict[str, Any] | ServerResponse:
    """Validate JSON body against ``schema``; return body or error response."""
    if request.body is None:
        return errors.empty_body()

    messages = list(schema.validate_state(request.body))
    if extra_errors:
        messages.extend(extra_errors)

    if messages:
        return errors.validation_failed(schema_errors_to_details(messages))
    return request.body


def validate_query_dict(
    query: dict[str, Any],
    schema: DictStateSchema,
) -> dict[str, Any] | ServerResponse:
    """Validate a coerced query mapping."""
    messages = schema.validate_state(query)
    if messages:
        return errors.validation_failed(schema_errors_to_details(messages))
    return query


def _split_schema_error(message: str) -> tuple[str, str]:
    if message.startswith("missing required key: "):
        field = message.removeprefix("missing required key: ")
        return field, "is required"
    if ": " in message:
        field, text = message.split(": ", 1)
        return field, text
    return "body", message
