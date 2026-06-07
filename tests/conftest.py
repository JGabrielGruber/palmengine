"""
Shared fixtures for integration tests outside ``tests/core/``.

Core-only fixtures live in :mod:`tests.core.conftest` and apply under ``tests/core/``.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from palm.core.event import EventEngine


@pytest.fixture
def event_engine() -> Iterator[EventEngine]:
    """Initialized event bus for integration tests."""
    engine = EventEngine()
    engine.initialize()
    yield engine
    engine.shutdown()