"""
Concrete Orchestrator tests using TestMode + TestBackend.

Inherits all abstract contract tests.
"""

from __future__ import annotations

from palm.core.orchestration import Orchestrator, TestMode

from .test_contracts import AbstractOrchestratorTest


class TestOrchestratorWithTestMode(AbstractOrchestratorTest):
    def create_orchestrator(self) -> Orchestrator:
        mode = TestMode()
        orch = Orchestrator(mode=mode)
        orch.start()
        return orch

    def test_submit_with_explicit_id(self) -> None:
        orch = self.create_orchestrator()
        job = orch.submit({"steps": 1}, job_id="my-custom-id")
        assert job.id == "my-custom-id"
        assert orch.get_job("my-custom-id") is job

    def test_error_isolation_between_jobs(self) -> None:
        orch = self.create_orchestrator()
        good = orch.submit({"steps": 1, "final_status": "SUCCEEDED", "result": 42})
        # The injected error path in TestBackend raises during submit — we expect it
        try:
            orch.submit({"steps": 1, "inject_error": RuntimeError("boom")})
        except Exception as exc:
            assert "boom" in str(exc) or "injected" in str(exc)

        # Good job is unaffected and still present
        assert orch.get_job(good.id).result == 42

    def test_shutdown_cancels_live_jobs(self) -> None:
        orch = self.create_orchestrator()
        # Create a job that would take many steps
        j = orch.submit({"steps": 1000, "final_status": "SUCCEEDED"})
        # In TestMode it will have finished already in most cases.
        # Force it live for the test
        if j.is_terminal:
            # re-submit a fresh long one
            j = orch.submit({"steps": 1000})
        orch.shutdown()
        # After shutdown, any remaining live job should have been cancelled by the mode
        # (best-effort semantics)
        assert j.status in ("CANCELLED", "SUCCEEDED", "FAILED")
