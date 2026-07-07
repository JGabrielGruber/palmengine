"""Proposal repository factory — in-memory or storage-backed."""

from __future__ import annotations

from typing import Any

from palm.core.storage import StorageEngine
from palm.services.design.proposal import DesignProposalRepository
from palm.services.design.storage_proposal_repository import StorageDesignProposalRepository


def _storage_ready(storage: StorageEngine | None) -> bool:
    if storage is None:
        return False
    backend = storage.backend
    return backend is not None and backend.is_open


def create_proposal_repository(storage: StorageEngine | None = None) -> Any:
    """Return a proposal repository using storage when initialized."""
    if _storage_ready(storage):
        return StorageDesignProposalRepository(storage)
    return DesignProposalRepository()


__all__ = ["create_proposal_repository"]