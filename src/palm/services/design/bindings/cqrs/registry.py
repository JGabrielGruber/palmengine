"""Design service CQRS registry — command/query catalog for host wiring."""

from __future__ import annotations

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

DESIGN_COMMAND_TYPES: tuple[type, ...] = (
    ProposeFlowDefinitionCommand,
    CommitDesignProposalCommand,
    DiscardDesignProposalCommand,
)

DESIGN_QUERY_TYPES: tuple[type, ...] = (
    GetDesignProposalQuery,
    ListDesignProposalsQuery,
    ValidateDesignProposalQuery,
    AnalyzeDesignProposalImpactQuery,
)


__all__ = [
    "DESIGN_COMMAND_TYPES",
    "DESIGN_QUERY_TYPES",
]