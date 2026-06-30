"""Studio definition persistence — register flows and processes in the repository."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.common.runtimes.server.protocol import ServerRequest, ServerResponse
from palm.common.services.views import flow_detail, process_detail
from palm.definitions.flow import FlowDefinition
from palm.definitions.process import ProcessDefinition

if TYPE_CHECKING:
    from palm.common.runtimes.server.context import ServerContext


def _parse_flow(body: dict[str, Any]) -> FlowDefinition | ServerResponse:
    try:
        return FlowDefinition.from_dict(body)
    except (KeyError, TypeError, ValueError) as exc:
        return ServerResponse(
            status=400,
            body={"error": "invalid_request", "message": f"Invalid flow definition: {exc}"},
        )


def _parse_process(body: dict[str, Any]) -> ProcessDefinition | ServerResponse:
    try:
        return ProcessDefinition.from_dict(body)
    except (KeyError, TypeError, ValueError) as exc:
        return ServerResponse(
            status=400,
            body={"error": "invalid_request", "message": f"Invalid process definition: {exc}"},
        )


def save_flow(ctx: ServerContext, request: ServerRequest) -> ServerResponse:
    """Register a flow definition in the DefinitionRepository."""
    body = request.body
    if not isinstance(body, dict):
        return ServerResponse(
            status=400,
            body={"error": "invalid_request", "message": "JSON object body required"},
        )

    parsed = _parse_flow(body)
    if isinstance(parsed, ServerResponse):
        return parsed

    repository = ctx.runtime.repository
    repository.register_flow(parsed)
    return ServerResponse(
        status=200,
        body={
            "saved": True,
            "kind": "flow",
            "flow": flow_detail(parsed),
        },
    )


def save_process(ctx: ServerContext, request: ServerRequest) -> ServerResponse:
    """Register a process definition in the DefinitionRepository."""
    body = request.body
    if not isinstance(body, dict):
        return ServerResponse(
            status=400,
            body={"error": "invalid_request", "message": "JSON object body required"},
        )

    parsed = _parse_process(body)
    if isinstance(parsed, ServerResponse):
        return parsed

    repository = ctx.runtime.repository
    repository.register_process(parsed)
    for flow in parsed.flows:
        repository.register_flow(flow)

    return ServerResponse(
        status=200,
        body={
            "saved": True,
            "kind": "process",
            "process": process_detail(parsed),
        },
    )
