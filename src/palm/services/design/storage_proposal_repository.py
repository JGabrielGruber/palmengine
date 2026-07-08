"""Durable design proposal storage via ``StorageEngine``."""

from __future__ import annotations

import threading
import uuid
from datetime import UTC, datetime
from typing import Any

from palm.common.exceptions import DesignProposalNotFoundError
from palm.core.exceptions import StorageNotConfiguredError
from palm.core.storage import StorageEngine
from palm.services.design.proposal import DesignProposal

_PREFIX = "palm:design:proposals"
_INDEX_KEY = f"{_PREFIX}:_index"
_OPEN = "open"


def _proposal_key(proposal_id: str) -> str:
    return f"{_PREFIX}:{proposal_id}"


def proposal_from_dict(data: dict[str, Any]) -> DesignProposal:
    """Rehydrate a proposal from persisted storage."""
    return DesignProposal(
        proposal_id=str(data["proposal_id"]),
        body=dict(data.get("body") or {}),
        status=str(data.get("status") or _OPEN),
        kind=str(data.get("kind") or "flow"),
        base_flow_id=data.get("base_flow_id"),
        flow_id=data.get("flow_id"),
        base_resource_id=data.get("base_resource_id"),
        resource_id=data.get("resource_id"),
        validation=dict(data["validation"]) if isinstance(data.get("validation"), dict) else None,
        impact=dict(data["impact"]) if isinstance(data.get("impact"), dict) else None,
        committed_revision=data.get("committed_revision"),
        created_at=str(data.get("created_at") or datetime.now(UTC).isoformat()),
        updated_at=str(data.get("updated_at") or datetime.now(UTC).isoformat()),
    )


class StorageDesignProposalRepository:
    """CRUD for design proposals backed by ``StorageEngine``."""

    def __init__(self, storage: StorageEngine) -> None:
        self._storage = storage
        self._lock = threading.RLock()
        self._cache: dict[str, DesignProposal] = {}

    def create(
        self,
        body: dict[str, Any],
        *,
        kind: str = "flow",
        base_flow_id: str | None = None,
        flow_id: str | None = None,
        base_resource_id: str | None = None,
        resource_id: str | None = None,
    ) -> DesignProposal:
        proposal_id = f"prop-{uuid.uuid4().hex[:12]}"
        proposal = DesignProposal(
            proposal_id=proposal_id,
            body=dict(body),
            kind=str(kind),
            base_flow_id=base_flow_id,
            flow_id=flow_id or base_flow_id,
            base_resource_id=base_resource_id,
            resource_id=resource_id or base_resource_id,
        )
        return self.save(proposal)

    def save(self, proposal: DesignProposal) -> DesignProposal:
        proposal.updated_at = datetime.now(UTC).isoformat()
        with self._lock:
            self._cache[proposal.proposal_id] = proposal
            self._persist(proposal)
            if proposal.status == _OPEN:
                self._index_add(proposal.proposal_id)
            else:
                self._index_remove(proposal.proposal_id)
        return proposal

    def get(self, proposal_id: str) -> DesignProposal:
        with self._lock:
            cached = self._cache.get(proposal_id)
            if cached is not None:
                return cached
            raw = self._storage_get(_proposal_key(proposal_id))
        if raw is None:
            raise DesignProposalNotFoundError(proposal_id)
        proposal = proposal_from_dict(raw)
        with self._lock:
            self._cache[proposal_id] = proposal
        return proposal

    def delete(self, proposal_id: str) -> bool:
        with self._lock:
            existed = proposal_id in self._cache or self._storage_get(_proposal_key(proposal_id)) is not None
            self._cache.pop(proposal_id, None)
            try:
                self._storage_delete(_proposal_key(proposal_id))
            except StorageNotConfiguredError:
                return False
            self._index_remove(proposal_id)
        return existed

    def list_proposals(self, *, flow_id: str | None = None, status: str | None = _OPEN) -> list[DesignProposal]:
        with self._lock:
            ids = list(self._index_read())
        rows: list[DesignProposal] = []
        for proposal_id in ids:
            try:
                rows.append(self.get(proposal_id))
            except DesignProposalNotFoundError:
                self._index_remove(proposal_id)
        if flow_id is not None:
            rows = [row for row in rows if row.flow_id == flow_id or row.base_flow_id == flow_id]
        if status is not None:
            rows = [row for row in rows if row.status == status]
        return sorted(rows, key=lambda item: item.updated_at, reverse=True)

    def _persist(self, proposal: DesignProposal) -> None:
        self._storage_set(_proposal_key(proposal.proposal_id), proposal.to_dict())

    def _index_read(self) -> list[str]:
        raw = self._storage_get(_INDEX_KEY)
        if not isinstance(raw, list):
            return []
        return [str(item) for item in raw]

    def _index_add(self, proposal_id: str) -> None:
        ids = self._index_read()
        if proposal_id not in ids:
            ids.append(proposal_id)
            self._storage_set(_INDEX_KEY, ids)

    def _index_remove(self, proposal_id: str) -> None:
        ids = [item for item in self._index_read() if item != proposal_id]
        self._storage_set(_INDEX_KEY, ids)

    def _storage_get(self, key: str) -> Any | None:
        try:
            return self._storage.get(key)
        except StorageNotConfiguredError:
            return None

    def _storage_set(self, key: str, value: Any) -> None:
        self._storage.set(key, value)

    def _storage_delete(self, key: str) -> None:
        self._storage.delete(key)


__all__ = ["StorageDesignProposalRepository", "proposal_from_dict"]