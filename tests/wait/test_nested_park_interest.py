"""Nested park opens continue-plane interest (no set_child_wait façade)."""

from __future__ import annotations

from palm.core.orchestration.job_state import JobState
from palm.core.wait import WAIT_KIND_JOB, has_open_waits, list_wait_interests
from plugins.patterns.wizard.bindings.resource.nested_park import (
    NESTED_SOURCE,
    clear_nested_park,
    nested_park_interest,
    open_nested_park,
    park_meta_from_result,
)


def test_open_nested_park_writes_interest_only() -> None:
    state = JobState()
    park = park_meta_from_result(
        {
            "child_job_id": "child-abc",
            "instance_id": "inst-1",
            "status": "WAITING_FOR_INPUT",
        },
        step_slug="spawn",
        output_key="child_out",
        resource_ref="submit-child",
    )
    interest = open_nested_park(state, target_id=park["target_id"], meta=park["meta"])
    assert interest.kind == WAIT_KIND_JOB
    assert interest.target_id == "child-abc"
    assert interest.meta["source"] == NESTED_SOURCE
    assert interest.meta["step_slug"] == "spawn"
    assert nested_park_interest(state) is not None
    assert has_open_waits(state)


def test_clear_nested_park() -> None:
    state = JobState()
    open_nested_park(
        state,
        target_id="c-1",
        meta={"source": NESTED_SOURCE, "step_slug": "s", "output_key": "o"},
    )
    clear_nested_park(state, target_id="c-1")
    assert nested_park_interest(state) is None
    assert list_wait_interests(state) == []


def test_park_meta_requires_child_id() -> None:
    import pytest

    with pytest.raises(ValueError, match="child_job_id"):
        park_meta_from_result({}, step_slug="s", output_key="o")
