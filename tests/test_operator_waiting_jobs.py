"""Tests for waiting job list enrichment and slim MCP rows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from palm.common.operator.waiting_jobs import enrich_job_list_rows, slim_waiting_job_row


@dataclass(frozen=True)
class _Summary:
    instance_id: str
    job_id: str
    flow_name: str | None = None
    current_step_slug: str | None = None


class _FakeJob:
    def __init__(self, metadata: dict[str, Any]) -> None:
        self.metadata = metadata


class _FakeRuntime:
    def __init__(self, *, summaries: list[_Summary], jobs: dict[str, _FakeJob]) -> None:
        self._summaries = summaries
        self._jobs = jobs

    @property
    def instance_manager(self) -> _FakeRuntime:
        return self

    def list_summaries(self) -> list[_Summary]:
        return self._summaries

    def get_job(self, job_id: str) -> _FakeJob:
        return self._jobs[job_id]


def test_slim_waiting_job_row_never_uses_job_id_as_instance_id() -> None:
    row = {
        "job_id": "job-7bd386ce7f3c",
        "status": "WAITING_FOR_INPUT",
        "metadata": {},
    }
    slim = slim_waiting_job_row(row)
    assert slim["job_id"] == "job-7bd386ce7f3c"
    assert "instance_id" not in slim


def test_slim_waiting_job_row_uses_top_level_instance_id() -> None:
    row = {
        "job_id": "job-1",
        "instance_id": "inst-abc",
        "status": "WAITING_FOR_INPUT",
        "pattern": "wizard",
        "flow": "onboard",
        "step": "name",
        "metadata": {},
    }
    slim = slim_waiting_job_row(row)
    assert slim["instance_id"] == "inst-abc"
    assert slim["pattern"] == "wizard"
    assert slim["flow"] == "onboard"
    assert slim["step"] == "name"


def test_enrich_job_list_rows_resolves_instance_from_summary() -> None:
    runtime = _FakeRuntime(
        summaries=[
            _Summary(
                instance_id="inst-real",
                job_id="job-7bd386ce7f3c",
                flow_name="todo-builder",
                current_step_slug="goal",
            )
        ],
        jobs={
            "job-7bd386ce7f3c": _FakeJob(
                {
                    "pattern": "wizard",
                    "flow": "todo-builder",
                }
            ),
        },
    )
    rows = enrich_job_list_rows(
        runtime,
        [
            {
                "job_id": "job-7bd386ce7f3c",
                "status": "WAITING_FOR_INPUT",
                "metadata": {},
            }
        ],
    )
    assert rows[0]["instance_id"] == "inst-real"
    assert rows[0]["pattern"] == "wizard"
    assert rows[0]["flow"] == "todo-builder"
    assert rows[0]["step"] == "goal"