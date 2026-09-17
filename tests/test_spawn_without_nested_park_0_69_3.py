"""0.69.3 — spawn without nested park. Guidance stays operator-wait.

Park glue: start named work as a same-session sibling. The parked chooser
stays WAITING_FOR_INPUT. Do not open WaitInterest on the sibling.
Nested park (until_input) stays leftover — do not delete it.
Kit start() is a later slice.
"""

from __future__ import annotations

from palm.app.host.application_host import ApplicationHost
from palm.core.orchestration import JobStatus
from palm.core.wait import has_open_waits, list_wait_interests
from palm.patterns.wizard.bindings.resource.nested_park import nested_park_interest
from tests.helpers.flows import spine_wizard


def _instance_id(job) -> str:
    iid = str(job.metadata.get("instance_id") or "")
    assert iid
    return iid


def test_chooser_starts_waiting_for_input() -> None:
    host = ApplicationHost.for_mode("test")
    host.start()
    try:
        svc = host.session
        bound = svc.bind_surface(surface="embedded", origin="test")
        parent = host.submit_flow(spine_wizard("chooser"), job_id="job-chooser")
        parent_iid = _instance_id(parent)
        svc.attach_after_start(bound.session_id, parent_iid)

        assert parent.status == JobStatus.WAITING_FOR_INPUT
        assert nested_park_interest(parent.state) is None
        assert not has_open_waits(parent.state)
    finally:
        host.shutdown()


def test_spawn_sibling_leaves_parent_waiting_without_nested_park() -> None:
    host = ApplicationHost.for_mode("test")
    host.start()
    try:
        svc = host.session
        bound = svc.bind_surface(surface="embedded", origin="test")
        parent = host.submit_flow(spine_wizard("chooser"), job_id="job-chooser")
        parent_iid = _instance_id(parent)
        svc.attach_after_start(bound.session_id, parent_iid)

        surface = host.execution.flows.spawn_sibling(
            bound.session_id,
            spine_wizard("title"),
            job_id="job-title",
        )

        parent = host.runtime().orchestration.get_job("job-chooser")
        child = host.runtime().orchestration.get_job("job-title")
        child_iid = _instance_id(child)

        assert parent.status == JobStatus.WAITING_FOR_INPUT
        assert child.status == JobStatus.WAITING_FOR_INPUT
        assert "session_id" not in (child.metadata or {})
        assert nested_park_interest(parent.state) is None
        owned = svc.list_instances(bound.session_id)
        assert parent_iid in owned
        assert child_iid in owned
        assert surface.session_id == bound.session_id
        assert svc.active_instance(bound.session_id) == child_iid
    finally:
        host.shutdown()


def test_spawn_sibling_does_not_open_wait_interest_on_sibling() -> None:
    host = ApplicationHost.for_mode("test")
    host.start()
    try:
        svc = host.session
        bound = svc.bind_surface(surface="embedded", origin="test")
        parent = host.submit_flow(spine_wizard("chooser"), job_id="job-chooser")
        svc.attach_after_start(bound.session_id, _instance_id(parent))

        host.execution.flows.spawn_sibling(
            bound.session_id,
            spine_wizard("title"),
            job_id="job-title",
        )

        parent = host.runtime().orchestration.get_job("job-chooser")
        child = host.runtime().orchestration.get_job("job-title")
        child_iid = _instance_id(child)
        child_job_id = child.id

        assert not has_open_waits(parent.state)
        interests = list_wait_interests(parent.state)
        assert interests == []
        targets = {w.target_id for w in interests}
        assert child_job_id not in targets
        assert child_iid not in targets
    finally:
        host.shutdown()


def test_until_input_nested_park_leftover_still_opens_wait_on_child() -> None:
    """Leftover composition: until_input parks parent on child terminal.

    Not the floor path. Do not delete this slice.
    """
    import palm.providers  # noqa: F401 — register providers
    from palm.definitions import FlowDefinition, ResourceDefinition
    from palm.providers.palm.bindings.runtimes.wiring import clear_palm_runtime
    from palm.runtimes.embedded import EmbeddedRuntime

    child_flow = FlowDefinition(
        id="flow-child-wizard",
        name="child-wizard",
        pattern="wizard",
        options={
            "steps": [
                {"slug": "question", "title": "Question", "prompt": "Child question?"},
            ],
        },
    )
    parent_flow = FlowDefinition(
        id="flow-parent-wizard",
        name="parent-wizard",
        pattern="wizard",
        options={
            "steps": [
                {
                    "slug": "spawn_child",
                    "title": "Spawn Child Wizard",
                    "step_kind": "resource",
                    "resource_ref": "submit-child-wizard",
                    "output_key": "child_job",
                },
            ],
        },
    )
    resource = ResourceDefinition(
        id="resource-submit-child-wizard",
        name="submit-child-wizard",
        provider="palm",
        action="submit_flow",
        resource_id="flow:child-wizard",
        params={
            "wait": True,
            "wait_mode": "until_input",
            "timeout_seconds": 5,
        },
    )
    rt = EmbeddedRuntime()
    rt.start()
    try:
        rt.repository.save_flow(child_flow)
        rt.repository.save_flow(parent_flow)
        rt.repository.save_resource(resource)
        parent_job = rt.submit_flow("parent-wizard")
        rt.wait_until_idle(timeout=5)

        assert parent_job.status == JobStatus.WAITING_FOR_INPUT
        park = nested_park_interest(parent_job.state)
        assert park is not None
        assert has_open_waits(parent_job.state)
        assert park.target_id
        child_job = rt.get_job(str(park.target_id))
        assert child_job.status == JobStatus.WAITING_FOR_INPUT
    finally:
        rt.stop()
        clear_palm_runtime()
