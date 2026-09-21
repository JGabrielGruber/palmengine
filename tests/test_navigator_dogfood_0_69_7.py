"""0.69.7 — empty-handed start dogfood on embedded (floor proof).

One walk without Assist: bind → empty-handed start of navigator → stamp →
stay WAITING → sibling start (no job session_id, no WaitInterest) →
focus(guidance_instance_id) home. Seed is kit.guidance_definition_id after
bind. Do not invent env / settings types. Do not start operator-entry.
"""

from __future__ import annotations

import pytest

from examples.definitions.navigator import NAVIGATOR_FLOW, register_definitions
from examples.definitions.operator_entry import OPERATOR_ENTRY_FLOW
from examples.definitions.operator_entry import (
    register_definitions as register_operator_entry,
)
from palm.app.host.application_host import ApplicationHost
from palm.app.host.composition import composition_profile_from_name
from palm.common.job_inspection import JobContext
from palm.core.orchestration import JobStatus
from palm.core.wait import has_open_waits, list_wait_interests
from palm.kits.present import GUIDANCE_INSTANCE_ID
from tests.helpers.flows import spine_wizard

_ASSIST_ENVELOPE_KEYS = (
    "question",
    "handoff_ready",
    "inspect_catalog",
    "compose",
    "scenario_id",
    "operator_mode",
)


def _job(host: ApplicationHost, job_id: str):
    return host.runtime().orchestration.get_job(job_id)


def _focused_job(host: ApplicationHost, kit):
    iid = kit.bound.instance_id
    inst = host.runtime().get_instance(iid)
    return _job(host, inst.job_id), inst


def test_embedded_test_host_has_no_assist() -> None:
    host = ApplicationHost.for_mode("test")
    host.start()
    try:
        assert host.composition == composition_profile_from_name("embedded")
        assert "assist" not in host.composition.services
        assert host.assist is None
    finally:
        host.shutdown()


def test_unset_guidance_definition_id_still_refuses_empty_handed_start() -> None:
    from palm.kits.present import bind

    host = ApplicationHost.for_mode("test")
    host.start()
    try:
        register_definitions(host.runtime().repository)
        kit = bind(host, surface="embedded", origin="test")

        assert kit.guidance_definition_id is None
        with pytest.raises(RuntimeError, match="guidance_definition_id"):
            kit.start()

        assert kit.bound.instance_id is None
        assert host.session.list_instances(kit.bound.session_id) == []
    finally:
        host.shutdown()


def test_empty_handed_start_does_not_start_operator_entry() -> None:
    from palm.kits.present import bind

    host = ApplicationHost.for_mode("test")
    host.start()
    try:
        register_definitions(host.runtime().repository)
        register_operator_entry(host.runtime().repository)
        kit = bind(host, surface="embedded", origin="test")
        kit.guidance_definition_id = NAVIGATOR_FLOW.definition_id

        kit.start()
        job, inst = _focused_job(host, kit)

        assert inst.flow_id == NAVIGATOR_FLOW.definition_id
        assert inst.flow_id != OPERATOR_ENTRY_FLOW.definition_id
        assert getattr(inst, "flow_name", None) != "operator-entry"
        assert job.status == JobStatus.WAITING_FOR_INPUT
    finally:
        host.shutdown()


def test_present_waiting_navigator_has_no_assist_envelope() -> None:
    from palm.kits.present import bind

    host = ApplicationHost.for_mode("test")
    host.start()
    try:
        register_definitions(host.runtime().repository)
        kit = bind(host, surface="embedded", origin="test")
        kit.guidance_definition_id = NAVIGATOR_FLOW.definition_id
        kit.start()

        turn = kit.present()

        assert isinstance(turn, JobContext)
        assert turn.pattern == "wizard"
        payload = {k: getattr(turn, k) for k in turn.__dataclass_fields__}
        for key in _ASSIST_ENVELOPE_KEYS:
            assert key not in payload
        assert host.assist is None
    finally:
        host.shutdown()


def test_floor_walk_empty_handed_navigator_on_embedded() -> None:
    from palm.kits.present import bind

    host = ApplicationHost.for_mode("test")
    host.start()
    try:
        register_definitions(host.runtime().repository)
        kit = bind(host, surface="embedded", origin="test")
        kit.guidance_definition_id = NAVIGATOR_FLOW.definition_id

        surface = kit.start()
        home = surface.instance_id
        assert home
        parent_job, inst = _focused_job(host, kit)
        assert inst.flow_id == "navigator"
        assert kit.bound.metadata[GUIDANCE_INSTANCE_ID] == home
        assert parent_job.status == JobStatus.WAITING_FOR_INPUT
        assert "session_id" not in (parent_job.metadata or {})

        kit.start(spine_wizard("title"), job_id="job-title")
        title = kit.bound.instance_id
        child = _job(host, "job-title")
        child_iid = str(child.metadata.get("instance_id") or "")
        owned = host.session.list_instances(kit.bound.session_id)

        assert title and title != home
        assert child_iid == title
        assert "session_id" not in (child.metadata or {})
        assert not has_open_waits(parent_job.state)
        interests = list_wait_interests(parent_job.state)
        targets = {w.target_id for w in interests}
        assert child.id not in targets
        assert child_iid not in targets
        assert parent_job.status == JobStatus.WAITING_FOR_INPUT
        assert home in owned
        assert title in owned
        assert host.session.active_instance(kit.bound.session_id) == title
        assert kit.bound.metadata[GUIDANCE_INSTANCE_ID] == home

        focused = kit.focus(home)
        assert focused.instance_id == home
        assert kit.bound.instance_id == home
        assert host.session.active_instance(kit.bound.session_id) == home
        assert kit.bound.metadata[GUIDANCE_INSTANCE_ID] == home
        assert _focused_job(host, kit)[0].status == JobStatus.WAITING_FOR_INPUT
    finally:
        host.shutdown()
