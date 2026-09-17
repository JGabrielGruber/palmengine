"""0.69.6 — navigator wizard pack beside operator_entry.

New catalog chooser: stays WAITING_FOR_INPUT after naming work. Named
work is a same-session sibling (kit start / spawn_sibling). Return is
focus of guidance_instance_id. Do not migrate operator_entry.
"""

from __future__ import annotations

from examples.definitions.navigator import NAVIGATOR_FLOW, register_definitions
from examples.definitions.operator_entry import OPERATOR_ENTRY_FLOW
from examples.definitions.operator_entry import (
    register_definitions as register_operator_entry,
)
from palm.app.host.application_host import ApplicationHost
from palm.core.orchestration import JobStatus
from palm.core.wait import has_open_waits, list_wait_interests
from palm.system.subsystems.planes.session.walk_writes import GUIDANCE_INSTANCE_ID
from tests.helpers.flows import spine_wizard


def _job(host: ApplicationHost, job_id: str):
    return host.runtime().orchestration.get_job(job_id)


def test_navigator_pack_sits_beside_operator_entry() -> None:
    host = ApplicationHost.for_mode("test")
    host.start()
    try:
        repo = host.runtime().repository
        register_definitions(repo)
        register_operator_entry(repo)

        nav = repo.get_flow("navigator", by_id=True)
        leftover = repo.get_flow("flow-palm-operator-entry", by_id=True)

        assert nav.definition_id == "navigator"
        assert nav.pattern == "wizard"
        assert leftover.definition_id == OPERATOR_ENTRY_FLOW.definition_id
        options = nav.options or {}
        assist = (options.get("metadata") or {}).get("assist") or {}
        assert "handoff_map" not in assist
        assert "handoff_flows" not in assist
        routes: list[str] = []
        for step in options.get("steps") or []:
            if not isinstance(step, dict):
                continue
            params = step.get("params") or {}
            route = params.get("route_on_answer") or {}
            if isinstance(route, dict):
                routes.extend(str(v) for v in route.values())
        assert "__end__" not in routes
    finally:
        host.shutdown()


def test_naming_work_on_navigator_stays_waiting() -> None:
    from palm.kits.present import bind

    host = ApplicationHost.for_mode("test")
    host.start()
    try:
        register_definitions(host.runtime().repository)
        kit = bind(host, surface="embedded", origin="test")
        kit.guidance_definition_id = NAVIGATOR_FLOW.definition_id

        kit.start(NAVIGATOR_FLOW, job_id="job-nav")
        kit.submit("title")

        parent = _job(host, "job-nav")
        assert parent.status == JobStatus.WAITING_FOR_INPUT
    finally:
        host.shutdown()


def test_named_work_is_same_session_sibling_without_wait_interest() -> None:
    from palm.kits.present import bind

    host = ApplicationHost.for_mode("test")
    host.start()
    try:
        register_definitions(host.runtime().repository)
        kit = bind(host, surface="embedded", origin="test")
        kit.guidance_definition_id = NAVIGATOR_FLOW.definition_id
        kit.start(NAVIGATOR_FLOW, job_id="job-nav")
        parent_iid = kit.bound.instance_id
        assert parent_iid

        kit.submit("title")
        kit.start(spine_wizard("title"), job_id="job-title")

        parent = _job(host, "job-nav")
        child = _job(host, "job-title")
        child_iid = str(child.metadata.get("instance_id") or "")
        owned = host.session.list_instances(kit.bound.session_id)

        assert parent.status == JobStatus.WAITING_FOR_INPUT
        assert "session_id" not in (child.metadata or {})
        assert not has_open_waits(parent.state)
        interests = list_wait_interests(parent.state)
        targets = {w.target_id for w in interests}
        assert child.id not in targets
        assert child_iid not in targets
        assert parent_iid in owned
        assert child_iid in owned
    finally:
        host.shutdown()


def test_return_home_is_focus_of_guidance_instance_id() -> None:
    from palm.kits.present import bind

    host = ApplicationHost.for_mode("test")
    host.start()
    try:
        register_definitions(host.runtime().repository)
        kit = bind(host, surface="embedded", origin="test")
        kit.guidance_definition_id = NAVIGATOR_FLOW.definition_id
        kit.start(NAVIGATOR_FLOW, job_id="job-nav")
        home = kit.bound.metadata[GUIDANCE_INSTANCE_ID]
        assert home

        kit.start(spine_wizard("title"), job_id="job-title")
        title = kit.bound.instance_id
        assert title and title != home
        assert host.session.active_instance(kit.bound.session_id) == title

        surface = kit.focus(home)

        assert surface.instance_id == home
        assert kit.bound.instance_id == home
        assert host.session.active_instance(kit.bound.session_id) == home
        assert kit.bound.metadata[GUIDANCE_INSTANCE_ID] == home
        assert _job(host, "job-nav").status == JobStatus.WAITING_FOR_INPUT
    finally:
        host.shutdown()


def test_operator_entry_leftover_still_ends() -> None:
    from palm.kits.present import bind

    host = ApplicationHost.for_mode("test")
    host.start()
    try:
        register_operator_entry(host.runtime().repository)
        kit = bind(host, surface="embedded", origin="test")
        kit.start(OPERATOR_ENTRY_FLOW, job_id="job-oe")
        kit.submit("todo-builder")

        leftover = _job(host, "job-oe")
        assert leftover.status != JobStatus.WAITING_FOR_INPUT
    finally:
        host.shutdown()
