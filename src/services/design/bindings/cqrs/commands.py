"""Design service CQRS command types (transport only)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from palm.common.cqrs.command import Command


@dataclass(frozen=True)
class ProposeFlowDefinitionCommand(Command):
    """Create a design proposal from a flow body."""

    body: dict[str, Any]
    base_flow_id: str | None = None


@dataclass(frozen=True)
class CommitDesignProposalCommand(Command):
    """Publish a validated design proposal revision."""

    proposal_id: str
    commit_token: str | None = None
    input_token: str | None = None


@dataclass(frozen=True)
class DiscardDesignProposalCommand(Command):
    """Discard an open design proposal."""

    proposal_id: str


__all__ = [
    "CommitDesignProposalCommand",
    "DiscardDesignProposalCommand",
    "ProposeFlowDefinitionCommand",
]