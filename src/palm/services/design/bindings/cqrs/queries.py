"""Design service CQRS query types (transport only)."""

from __future__ import annotations

from dataclasses import dataclass

from palm.common.cqrs.query import Query


@dataclass(frozen=True)
class GetDesignProposalQuery(Query):
    """Load a design proposal envelope."""

    proposal_id: str


@dataclass(frozen=True)
class ListDesignProposalsQuery(Query):
    """List open design proposals."""

    flow_id: str | None = None


@dataclass(frozen=True)
class ValidateDesignProposalQuery(Query):
    """Validate a design proposal (dry-run by default)."""

    proposal_id: str
    dry_run: bool = True


@dataclass(frozen=True)
class AnalyzeDesignProposalImpactQuery(Query):
    """Analyze instance impact for a proposal commit."""

    proposal_id: str


__all__ = [
    "AnalyzeDesignProposalImpactQuery",
    "GetDesignProposalQuery",
    "ListDesignProposalsQuery",
    "ValidateDesignProposalQuery",
]