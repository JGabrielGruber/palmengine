"""Fixtures for ``tests.common`` — reuses core test doubles."""

from __future__ import annotations

import pytest

from tests.core.fakes import TestState


@pytest.fixture
def test_state() -> TestState:
    return TestState()
