"""
Concrete tests for the Job abstraction and its status machine.
"""

from __future__ import annotations

import pytest

from palm.core.orchestration import Job, JobStatus
from palm.core.orchestration.exceptions import InvalidJobTransitionError


def test_job_basic_creation() -> None:
    j = Job(id="j1", executable={"steps": 1})
    assert j.status == JobStatus.PENDING
    assert not j.is_terminal
    assert j.is_live is False


def test_job_valid_transitions() -> None:
    j = Job(id="j1", executable={})
    j._allow_mutation = True
    j._transition_to(JobStatus.RUNNING)
    j._transition_to(JobStatus.WAITING_FOR_INPUT)
    j._transition_to(JobStatus.RUNNING)
    j._transition_to(JobStatus.SUCCEEDED)
    assert j.status == JobStatus.SUCCEEDED
    assert j.is_terminal


def test_job_invalid_transition_raises() -> None:
    j = Job(id="j1", executable={})
    j._allow_mutation = True
    j._transition_to(JobStatus.SUCCEEDED)
    with pytest.raises(InvalidJobTransitionError):
        j._transition_to(JobStatus.PENDING)  # terminal cannot go back to PENDING


def test_job_snapshot_contains_expected_keys() -> None:
    j = Job(id="j1", executable={"x": 1}, metadata={"tag": "test"})
    snap = j.snapshot()
    assert snap["id"] == "j1"
    assert snap["status"] == "PENDING"
    assert snap["metadata"]["tag"] == "test"
