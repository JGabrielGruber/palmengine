"""
Abstract resource provider contract.

Concrete providers (REST, GraphQL, Postgres) live in ``palm.providers``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseProvider(ABC):
    """Abstract external resource accessor."""

    def __init__(self, *, name: str) -> None:
        self.name = name

    @abstractmethod
    def connect(self) -> None:
        """Establish or validate the provider connection."""

    @abstractmethod
    def fetch(self, resource_id: str, **params: Any) -> Any:
        """Retrieve a resource by identifier."""

    @abstractmethod
    def disconnect(self) -> None:
        """Release provider resources."""
