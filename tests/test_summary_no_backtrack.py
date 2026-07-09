"""0.32.5 — summary confirm: human 'no' goes back, not validation error."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from palm.app import ApplicationHost, HostProfile
from palm.app.settings import PalmSettings
from palm.core.orchestration import JobStatus


@pytest.fixture
def host() -> Iterator[ApplicationHost]:
    settings = PalmSettings.for_tests(load_examples=False)
    h = ApplicationHost(settings=settings, profile=HostProfile.all_in_one())
    h.start()
    h.definitions.create_flow(
        {
            "id": "flow-summary-no-demo",
            "name": "summary-no-demo",
            "pattern": "wizard",
            "options": {
                "include_summary": True,
                "allow_backtrack": True,
                "steps": [
                    {
                        "slug": "name",
                        "title": "Name",
                        "prompt": "Name?",
                        "field_type": "text",
                    },
                ],
            },
        }
    )
    yield h
    h.shutdown()


def test_summary_no_backtracks_to_previous_step(host: ApplicationHost) -> None:
    sess = host.execution.flows.run_wizard({"flow_name": "summary-no-demo"})
    mid = sess.input("alice")
    assert mid.status == JobStatus.WAITING_FOR_INPUT.value
    detail = mid.detail or {}
    prompt = detail.get("prompt") if isinstance(detail.get("prompt"), dict) else {}
    assert prompt.get("step_kind") == "summary" or detail.get("step_kind") == "summary"

    after = sess.input("no")
    assert after.status == JobStatus.WAITING_FOR_INPUT.value
    d = after.detail or {}
    prompt2 = d.get("prompt") if isinstance(d.get("prompt"), dict) else {}
    step_kind = prompt2.get("step_kind") or d.get("step_kind")
    step = prompt2.get("step") or d.get("step") or d.get("slug")
    assert d.get("validation_error") in (None, "")
    assert step_kind == "input"
    assert step == "name"
