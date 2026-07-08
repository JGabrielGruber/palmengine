"""Registry-driven design command dispatch — handlers keyed by :func:`design_commands`."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from palm.services.design.grammar import resolve_design_command

if TYPE_CHECKING:
    from palm.services.design.service import DesignService

DispatchHandler = Callable[["DesignService", dict[str, Any], dict[str, str]], Any]

_PROPOSE_BODY_SKIP = frozenset(
    {"base_flow_id", "body", "commit_token", "input_token"},
)


def _handle_propose_flow(
    service: DesignService,
    params: dict[str, Any],
    _capture: dict[str, str],
) -> Any:
    body = dict(params.get("body") or params)
    base_flow_id = params.get("base_flow_id")
    payload = {
        key: value for key, value in body.items() if key not in _PROPOSE_BODY_SKIP
    }
    return service.propose_flow(payload, base_flow_id=base_flow_id)


def _handle_list_proposals(
    service: DesignService,
    params: dict[str, Any],
    _capture: dict[str, str],
) -> Any:
    return {"proposals": service.list_proposals(flow_id=params.get("flow_id"))}


def _handle_get_proposal(
    service: DesignService,
    _params: dict[str, Any],
    capture: dict[str, str],
) -> Any:
    return service.get_proposal(capture["proposal_id"])


def _handle_validate_proposal(
    service: DesignService,
    _params: dict[str, Any],
    capture: dict[str, str],
) -> Any:
    return service.validate_proposal(capture["proposal_id"], dry_run=True)


def _handle_analyze_impact(
    service: DesignService,
    _params: dict[str, Any],
    capture: dict[str, str],
) -> Any:
    return service.analyze_proposal_impact(capture["proposal_id"])


def _handle_commit_proposal(
    service: DesignService,
    params: dict[str, Any],
    capture: dict[str, str],
) -> Any:
    return service.commit_proposal(
        capture["proposal_id"],
        commit_token=params.get("commit_token"),
        input_token=params.get("input_token"),
    )


def _handle_discard_proposal(
    service: DesignService,
    _params: dict[str, Any],
    capture: dict[str, str],
) -> Any:
    return service.discard_proposal(capture["proposal_id"])


_DISPATCH_HANDLERS: dict[str, DispatchHandler] = {
    "propose_flow": _handle_propose_flow,
    "list_proposals": _handle_list_proposals,
    "get_proposal": _handle_get_proposal,
    "validate_proposal": _handle_validate_proposal,
    "analyze_impact": _handle_analyze_impact,
    "commit_proposal": _handle_commit_proposal,
    "discard_proposal": _handle_discard_proposal,
}


def dispatch_design_command(
    service: DesignService,
    path: list[str] | tuple[str, ...],
    params: dict[str, Any] | None = None,
) -> Any:
    """Execute a design command path using registry-driven handler lookup."""
    params = params or {}
    resolved = resolve_design_command(path)
    handler = _DISPATCH_HANDLERS.get(resolved.spec.command_id)
    if handler is None:
        raise RuntimeError(
            f"no dispatch handler registered for design command {resolved.spec.command_id!r}",
        )
    return handler(service, params, resolved.capture)


__all__ = ["dispatch_design_command"]