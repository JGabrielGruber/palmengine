"""Design proposal envelope and in-memory store (0.25 MVP)."""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from palm.common.exceptions import DesignProposalNotFoundError

_OPEN = "open"


@dataclass
class DesignProposal:
    """Draft flow definition change before revision publish."""

    proposal_id: str
    body: dict[str, Any]
    status: str = _OPEN
    base_flow_id: str | None = None
    flow_id: str | None = None
    validation: dict[str, Any] | None = None
    impact: dict[str, Any] | None = None
    committed_revision: int | None = None
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "status": self.status,
            "base_flow_id": self.base_flow_id,
            "flow_id": self.flow_id,
            "body": dict(self.body),
            "validation": dict(self.validation) if isinstance(self.validation, dict) else None,
            "impact": dict(self.impact) if isinstance(self.impact, dict) else None,
            "committed_revision": self.committed_revision,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class DesignProposalRepository:
    """In-memory CRUD for open design proposals."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._proposals: dict[str, DesignProposal] = {}

    def create(
        self,
        body: dict[str, Any],
        *,
        base_flow_id: str | None = None,
        flow_id: str | None = None,
    ) -> DesignProposal:
        proposal_id = f"prop-{uuid.uuid4().hex[:12]}"
        proposal = DesignProposal(
            proposal_id=proposal_id,
            body=dict(body),
            base_flow_id=base_flow_id,
            flow_id=flow_id or base_flow_id,
        )
        return self.save(proposal)

    def save(self, proposal: DesignProposal) -> DesignProposal:
        proposal.updated_at = datetime.now(UTC).isoformat()
        with self._lock:
            self._proposals[proposal.proposal_id] = proposal
        return proposal

    def get(self, proposal_id: str) -> DesignProposal:
        with self._lock:
            proposal = self._proposals.get(proposal_id)
        if proposal is None:
            raise DesignProposalNotFoundError(proposal_id)
        return proposal

    def delete(self, proposal_id: str) -> bool:
        with self._lock:
            return self._proposals.pop(proposal_id, None) is not None

    def list_proposals(self, *, flow_id: str | None = None, status: str | None = _OPEN) -> list[DesignProposal]:
        with self._lock:
            rows = list(self._proposals.values())
        if flow_id is not None:
            rows = [row for row in rows if row.flow_id == flow_id or row.base_flow_id == flow_id]
        if status is not None:
            rows = [row for row in rows if row.status == status]
        return sorted(rows, key=lambda item: item.updated_at, reverse=True)


def resolve_flow_id_from_body(body: dict[str, Any], *, base_flow_id: str | None = None) -> str | None:
    """Best-effort flow id from a proposal payload."""
    if base_flow_id:
        return str(base_flow_id)
    flow_section = body.get("flow")
    if isinstance(flow_section, dict):
        for key in ("definition_id", "id", "name"):
            value = flow_section.get(key)
            if value:
                return str(value)
    for key in ("definition_id", "flow_id", "flow_name", "name"):
        value = body.get(key)
        if value:
            return str(value)
    return None


__all__ = [
    "DesignProposal",
    "DesignProposalRepository",
    "resolve_flow_id_from_body",
]