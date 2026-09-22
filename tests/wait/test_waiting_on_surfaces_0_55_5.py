"""0.55.5 — waiting_on on inspect / list-waiting / doctor / Assist helpers."""

from __future__ import annotations

from palm.common.job_inspection import inspect_job_json
from palm.common.operator.waiting_jobs import enrich_job_list_rows, slim_waiting_job_row
from plugins.kits.server.diagnostics import build_doctor_report
from palm.system.subsystems.planes.wait.present import summarize_waiting_on, waiting_on_from_job
from palm.core.orchestration import Job, JobStatus
from palm.core.wait import make_job_wait, open_wait_on_job
from plugins.patterns.wizard.bindings.resource.nested_park import open_nested_park
from palm.services.assist.present.humanize import hint_text, question_text


def test_waiting_on_row_and_from_job() -> None:
    job = Job(id="owner", executable=None)
    open_wait_on_job(
        job,
        make_job_wait(
            "child-1",
            meta={"source": "nested_wizard", "step_slug": "spawn"},
        ),
    )
    rows = waiting_on_from_job(job)
    assert len(rows) == 1
    assert rows[0]["kind"] == "job"
    assert rows[0]["target_id"] == "child-1"
    assert rows[0]["source"] == "nested_wizard"
    assert rows[0]["step_slug"] == "spawn"
    summary = summarize_waiting_on(rows)
    assert summary is not None
    assert summary["count"] == 1
    assert summary["target_id"] == "child-1"


def test_inspect_job_json_includes_waiting_on() -> None:
    job = Job(id="owner-2", executable=None)
    open_wait_on_job(job, make_job_wait("c-9"))
    payload = inspect_job_json(job)
    assert payload["waiting_on"][0]["target_id"] == "c-9"


def test_enrich_and_slim_waiting_rows() -> None:
    job = Job(id="job-wait", executable=None)
    job.status = JobStatus.WAITING_FOR_INPUT
    job.metadata = {"instance_id": "inst-1", "pattern": "wizard", "flow": "parent"}
    open_wait_on_job(job, make_job_wait("child-x", meta={"source": "nested_wizard"}))

    class _Rt:
        def get_job(self, job_id: str) -> Job:
            assert job_id == "job-wait"
            return job

        @property
        def instance_manager(self) -> None:
            return None

    rows = enrich_job_list_rows(
        _Rt(),
        [{"job_id": "job-wait", "status": "WAITING_FOR_INPUT", "metadata": dict(job.metadata)}],
    )
    assert rows[0]["waiting_on"][0]["target_id"] == "child-x"
    assert rows[0]["waiting_on_summary"]["target_id"] == "child-x"
    slim = slim_waiting_job_row(rows[0])
    assert slim["waiting_on"][0]["kind"] == "job"
    assert slim["instance_id"] == "inst-1"


def test_doctor_reactive_interests_section() -> None:
    job = Job(id="parked", executable=None)
    job.status = JobStatus.WAITING_FOR_INPUT
    open_wait_on_job(job, make_job_wait("t-1"))

    class _Orch:
        def list_jobs(self) -> list[Job]:
            return [job]

    class _Storage:
        backend_name = "memory"
        backend = type("B", (), {"is_open": True})()

    class _Rt:
        runtime_name = "TestRuntime"
        auth_enforce = False
        storage = _Storage()
        orchestration = _Orch()
        repository = None
        wait_matcher = object()

    report = build_doctor_report(_Rt())
    assert report["jobs"]["open_wait_owners"] == 1
    assert report["jobs"]["open_wait_interests"] == 1
    assert report["reactive_interests"]["wait_matcher_wired"] is True
    assert report["reactive_interests"]["wait_kinds"]["job"] == 1
    assert "start" in report["reactive_interests"]["verbs"]


def test_assist_humanize_waiting_on() -> None:
    composed = {
        "waiting_on": [{"kind": "job", "target_id": "child-7"}],
    }
    assert "child-7" in question_text(composed)
    assert "complete" in hint_text(composed).lower() or "unparks" in hint_text(composed).lower()


def test_nested_park_surfaces_in_present() -> None:
    job = Job(id="p", executable=None)
    open_nested_park(
        job.state,
        target_id="nested-1",
        meta={
            "source": "nested_wizard",
            "step_slug": "spawn",
            "output_key": "out",
        },
    )
    rows = waiting_on_from_job(job)
    assert rows[0]["target_id"] == "nested-1"
    assert rows[0]["source"] == "nested_wizard"
