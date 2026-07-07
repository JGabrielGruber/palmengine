"""Design service CQRS handlers — thin transport over :class:`DesignService`."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.common.cqrs.command import Command
from palm.common.cqrs.query import Query
from palm.services.design.bindings.cqrs.commands import (
    CommitDesignProposalCommand,
    DiscardDesignProposalCommand,
    ProposeFlowDefinitionCommand,
)
from palm.services.design.bindings.cqrs.queries import (
    AnalyzeDesignProposalImpactQuery,
    GetDesignProposalQuery,
    ListDesignProposalsQuery,
    ValidateDesignProposalQuery,
)

if TYPE_CHECKING:
    from palm.services.design.service import DesignService


class DesignCommandHandler:
    """Dispatch design write commands to :class:`DesignService`."""

    def __init__(self, design: DesignService) -> None:
        self._design = design

    def handle(self, command: Command) -> Any:
        if isinstance(command, ProposeFlowDefinitionCommand):
            return self._design.propose_flow(
                command.body,
                base_flow_id=command.base_flow_id,
            )
        if isinstance(command, CommitDesignProposalCommand):
            return self._design.commit_proposal(
                command.proposal_id,
                commit_token=command.commit_token,
                input_token=command.input_token,
            )
        if isinstance(command, DiscardDesignProposalCommand):
            return self._design.discard_proposal(command.proposal_id)
        raise TypeError(f"Unsupported design command: {type(command).__name__}")


class DesignQueryHandler:
    """Dispatch design read queries to :class:`DesignService`."""

    def __init__(self, design: DesignService) -> None:
        self._design = design

    def ask(self, query: Query) -> Any:
        if isinstance(query, GetDesignProposalQuery):
            return self._design.get_proposal(query.proposal_id)
        if isinstance(query, ListDesignProposalsQuery):
            return self._design.list_proposals(flow_id=query.flow_id)
        if isinstance(query, ValidateDesignProposalQuery):
            return self._design.validate_proposal(
                query.proposal_id,
                dry_run=query.dry_run,
            )
        if isinstance(query, AnalyzeDesignProposalImpactQuery):
            return self._design.analyze_proposal_impact(query.proposal_id)
        raise TypeError(f"Unsupported design query: {type(query).__name__}")


__all__ = ["DesignCommandHandler", "DesignQueryHandler"]