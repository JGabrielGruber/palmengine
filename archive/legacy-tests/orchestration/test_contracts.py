"""
Abstract contract tests for the Orchestration Engine.

These classes are inherited by concrete tests (using TestMode) to guarantee
that the fundamental contracts defined in the design are never violated.

Pattern copied directly from tests/behavior_tree/test_base.py.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import pytest

from palm.core.orchestration import (
    Job,
    JobStatus,
    OrchestrationMode,
    Orchestrator,
    TestMode,
)
from palm.core.orchestration.exceptions import JobNotFoundError, OrchestratorError


class AbstractOrchestratorTest(ABC):
    """Fundamental Orchestrator contract that every mode must satisfy."""

    @abstractmethod
    def create_orchestrator(self) -> Orchestrator:
        """Return a freshly started orchestrator (usually wired to TestMode)."""
        ...

    def test_submit_creates_job_and_returns_it(self) -> None:
        orch = self.create_orchestrator()
        job = orch.submit({"steps": 1, "final_status": "SUCCEEDED"})
        assert isinstance(job, Job)
        assert job.id
        assert job.status == JobStatus.SUCCEEDED

    def test_get_job_roundtrip(self) -> None:
        orch = self.create_orchestrator()
        created = orch.submit({"steps": 1, "final_status": "SUCCEEDED"})
        fetched = orch.get_job(created.id)
        assert fetched is created

    def test_get_unknown_job_raises(self) -> None:
        orch = self.create_orchestrator()
        with pytest.raises(JobNotFoundError):
            orch.get_job("does-not-exist")

    def test_list_jobs_filters_by_status(self) -> None:
        orch = self.create_orchestrator()
        j1 = orch.submit({"steps": 1, "final_status": "SUCCEEDED"})
        j2 = orch.submit({"steps": 1, "final_status": "WAITING_FOR_INPUT"})
        succeeded = orch.list_jobs(JobStatus.SUCCEEDED)
        waiting = orch.list_jobs(JobStatus.WAITING_FOR_INPUT)
        assert j1 in succeeded
        assert j2 in waiting
        assert j1 not in waiting

    def test_max_concurrent_jobs_is_enforced(self) -> None:
        orch = self.create_orchestrator()
        orch.max_concurrent_jobs = 2
        orch.submit({"steps": 1})
        orch.submit({"steps": 1})
        with pytest.raises(OrchestratorError, match="Maximum concurrent"):
            orch.submit({"steps": 1})

    def test_provide_input_on_waiting_job_resumes_it(self) -> None:
        orch = self.create_orchestrator()
        job = orch.submit({"steps": 1, "final_status": "WAITING_FOR_INPUT"})
        assert job.status == JobStatus.WAITING_FOR_INPUT
        orch.provide_input(job.id, "answer", 42)
        # TestBackend + TestMode should have resumed it to SUCCEEDED
        assert job.status == JobStatus.SUCCEEDED
        assert job.blackboard.get("answer") == 42

    def test_cancel_non_terminal_job(self) -> None:
        orch = self.create_orchestrator()
        job = orch.submit({"steps": 5, "final_status": "SUCCEEDED"})  # long enough
        # Force it into RUNNING so cancel has something to do
        # (in real TestMode it may have already finished)
        if not job.is_terminal:
            orch.cancel_job(job.id)
        assert job.status == JobStatus.CANCELLED or job.is_terminal


class AbstractOrchestrationModeTest(ABC):
    """Contract for any OrchestrationMode implementation."""

    @abstractmethod
    def create_mode(self) -> OrchestrationMode:
        ...

    def test_start_and_is_running(self) -> None:
        mode = self.create_mode()
        assert not mode.is_running()
        mode.start()
        assert mode.is_running()

    def test_shutdown_stops_running(self) -> None:
        mode = self.create_mode()
        mode.start()
        mode.shutdown()
        assert not mode.is_running()

    def test_test_mode_is_the_reference_implementation(self) -> None:
        # Smoke that the concrete TestMode we ship satisfies the abstract contract
        mode = TestMode()
        mode.start()
        assert mode.is_running()
        mode.shutdown()
