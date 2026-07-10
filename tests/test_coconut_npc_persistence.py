"""Cross-session persistence for coconut-npc via kv provider."""

from __future__ import annotations

import palm.providers  # noqa: F401 — register providers
from examples.definitions.coconut.npc import COCONUT_NPC_FLOW
from examples.definitions.coconut.resources import (
    LOAD_COCONUT_PLAYER,
    SAVE_COCONUT_PLAYER,
    register_definitions as register_coconut_resources,
)

from palm.common.resource.document_storage import (
    build_memory_key,
    clear_memory_kv_store,
    get_memory_kv_store,
)
from palm.core.orchestration import JobStatus
from palm.patterns.wizard.bindings.context.keys import WizardKeys
from palm.providers.kv.provider import KvProvider
from palm.providers.palm.bindings.runtimes.wiring import bind_palm_runtime, clear_palm_runtime
from palm.runtimes.embedded import EmbeddedRuntime


def _register_coconut(rt: EmbeddedRuntime) -> None:
    rt.repository.save_flow(COCONUT_NPC_FLOW)
    rt.repository.save_resource(LOAD_COCONUT_PLAYER)
    rt.repository.save_resource(SAVE_COCONUT_PLAYER)
    register_coconut_resources(rt.repository)


def _drive_coconut_visit(
    rt: EmbeddedRuntime,
    *,
    player_name: str,
    reputation: str = "friend",
    exit_via: str = "leave",
) -> None:
    job = rt.submit_flow("coconut-npc")
    rt.wait_until_idle(timeout=10)
    idle_rounds = 0
    while job.status not in {JobStatus.SUCCEEDED, JobStatus.FAILED, JobStatus.CANCELLED}:
        if job.status != JobStatus.WAITING_FOR_INPUT:
            rt.wait_until_idle(timeout=10)
            job = rt.get_job(job.id)
            idle_rounds += 1
            if idle_rounds > 50:
                raise AssertionError(f"job stuck in {job.status}")
            continue
        step = job.state.get(WizardKeys.CURRENT_STEP)
        if step == "player_name":
            rt.provide_input(job.id, player_name)
        elif step == "reputation":
            rt.provide_input(job.id, reputation)
        elif step == "topic":
            rt.provide_input(job.id, exit_via)
        elif step == "farewell":
            rt.provide_input(job.id, "bye")
        else:
            raise AssertionError(f"unexpected waiting step {step!r}")
        rt.wait_until_idle(timeout=10)
        job = rt.get_job(job.id)
    assert job.status == JobStatus.SUCCEEDED, job.state.get(WizardKeys.RESOURCE_FEEDBACK)


def test_coconut_profile_persisted_in_kv_memory() -> None:
    rt = EmbeddedRuntime()
    rt.start()
    bind_palm_runtime(rt)
    try:
        _register_coconut(rt)
        _drive_coconut_visit(rt, player_name="Ada", reputation="friend")

        provider = KvProvider(name="kv")
        result = provider.invoke(
            "get",
            resource_id="players/Ada",
            params={"namespace": "coconut", "backend": "memory", "default": {}},
        )
        assert result.success is True
        assert result.data["found"] is True
        profile = result.data["value"]
        assert profile["visit_count"] == 1
        assert profile["reputation"] == "friend"
        assert profile["player_name"] == "Ada"
    finally:
        rt.stop()
        clear_palm_runtime()


def test_coconut_cross_session_visit_count_and_returning_greeting() -> None:
    rt = EmbeddedRuntime()
    rt.start()
    bind_palm_runtime(rt)
    try:
        _register_coconut(rt)
        _drive_coconut_visit(rt, player_name="Lyra", reputation="stranger")

        job = rt.submit_flow("coconut-npc")
        rt.wait_until_idle(timeout=10)
        while job.state.get(WizardKeys.CURRENT_STEP) != "topic":
            if job.status == JobStatus.WAITING_FOR_INPUT:
                step = job.state.get(WizardKeys.CURRENT_STEP)
                if step == "player_name":
                    rt.provide_input(job.id, "Lyra")
                else:
                    raise AssertionError(f"expected topic (returning skip), at {step!r}")
            rt.wait_until_idle(timeout=10)
            job = rt.get_job(job.id)

        answers = job.state.get(WizardKeys.ANSWERS) or {}
        profile = answers.get("player_profile") or {}
        assert profile.get("visit_count") == 2
        assert answers.get("is_returning") is True
        assert answers.get("reputation") == "stranger"
        greeting = answers.get("greeting_line") or ""
        assert "remember you" in greeting.lower()
        topic_prompt = str(answers.get("topic_prompt") or "").lower()
        assert "stranger" in topic_prompt
        assert job.state.get(WizardKeys.CURRENT_STEP) == "topic"

        stored = get_memory_kv_store().get(build_memory_key("coconut", "players/Lyra"))
        assert stored is not None
        assert stored["visit_count"] == 2
    finally:
        rt.stop()
        clear_palm_runtime()