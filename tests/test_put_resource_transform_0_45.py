"""0.45.1 — put_resource transform rule."""

from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import MagicMock

import pytest

from palm.common.transforms import autoload
from palm.core.exceptions import TransformApplicationError
from palm.core.resource.result import ProviderResult
from palm.core.transform.base import TransformMode
from palm.core.transform.engine import TransformEngine
from palm.common.transforms.rules.put_resource import PutResourceRule
from palm.core.transform.registry import transform_registry
from tests.core.fakes import TestState


@pytest.fixture(autouse=True)
def _rules() -> None:
    transform_registry.clear()
    autoload()


@pytest.fixture
def transform_engine() -> Iterator[TransformEngine]:
    engine = TransformEngine()
    engine.initialize()
    yield engine
    engine.shutdown()


def test_put_resource_is_batch_mode() -> None:
    assert PutResourceRule.mode is TransformMode.BATCH


def test_put_resource_invokes_engine(transform_engine) -> None:
    engine = MagicMock()
    engine.invoke.return_value = ProviderResult.ok(
        {"stored": True},
        action="put",
        resource_id="log/key",
    )
    state = TestState()
    state.set("events", [{"id": "e1"}])

    transform_engine.apply_to_state(
        "put_resource",
        state,
        "events",
        resource="my-log",
        resource_engine=engine,
    )
    engine.invoke.assert_called_once()
    call = engine.invoke.call_args
    assert call.kwargs["resource_ref"] == "my-log"
    assert call.kwargs["action"] == "put"
    assert call.kwargs["params"]["value"] == [{"id": "e1"}]


def test_put_resource_requires_engine(transform_engine) -> None:
    state = TestState()
    state.set("data", {"x": 1})
    with pytest.raises(TransformApplicationError, match="resource_engine"):
        transform_engine.apply_to_state("put_resource", state, "data", resource="r")