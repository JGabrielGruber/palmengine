#!/usr/bin/env python3
"""
End-to-end Palm demo — definitions, submit, wizard input, commit, resume.

Run from the repository root::

    uv run python examples/full_demo.py

The script simulates a process restart by stopping one ``EmbeddedRuntime`` and
starting another with the same ``StorageEngine``, then calling ``resume_process``.
"""

from __future__ import annotations

import sys
from typing import Any

import palm.patterns
import palm.providers
import palm.storages.memory  # noqa: F401
from palm.core import StorageEngine
from palm.core.orchestration import JobStatus
from palm.definitions import FlowDefinition
from palm.patterns.wizard.commit import CommitResult, default_commit_registry
from palm.patterns.wizard.keys import WizardKeys
from palm.runtimes.embedded import EmbeddedRuntime


def _register_demo_flow(repository: Any) -> FlowDefinition:
    default_commit_registry().register(
        "demo_commit",
        lambda ctx: CommitResult.success({"user": ctx.answers.get("name"), "committed": True}),
    )
    flow = FlowDefinition(
        id="flow-full-demo",
        name="full-demo",
        pattern="wizard",
        options={
            "include_summary": True,
            "include_commit": True,
            "commit_hook": "demo_commit",
            "steps": [
                {
                    "slug": "name",
                    "title": "Your name",
                    "prompt": "Enter your name",
                    "validation": [{"rule": "min_length", "params": {"min": 2}}],
                },
            ],
        },
    )
    repository.save_flow(flow)
    return flow


def _step_label(runtime: EmbeddedRuntime, job_id: str) -> str:
    slug = runtime.current_wizard_step(job_id)
    return slug or runtime.get_job(job_id).status.value


def _run_phase(title: str, fn: Any) -> None:
    print(f"\n=== {title} ===")
    fn()


def main() -> int:
    storage = StorageEngine()
    storage.initialize(backend="memory")

    instance_id: str | None = None

    def phase_one() -> None:
        nonlocal instance_id
        rt = EmbeddedRuntime(storage=storage)
        rt.start()
        try:
            _register_demo_flow(rt.repository)
            print("Registered flow 'full-demo' with commit handler 'demo_commit'")

            job = rt.submit_flow("full-demo")
            instance_id = str(job.metadata.get("instance_id", job.id))
            print(f"Submitted job {job.id[:12]}… → instance {instance_id[:12]}…")
            print(f"  step: {_step_label(rt, job.id)}")

            rt.provide_input(job.id, "River")
            print(f"  after name: {_step_label(rt, job.id)}")
            assert job.status == JobStatus.WAITING_FOR_INPUT

            rt.executor.persist_job(job)
            print("  persisted instance (simulating end of session)")
        finally:
            rt.stop()

    def phase_two() -> None:
        nonlocal instance_id
        if not instance_id:
            raise RuntimeError("phase one did not produce an instance_id")

        rt = EmbeddedRuntime(storage=storage)
        rt.start()
        try:
            _register_demo_flow(rt.repository)
            print(f"New runtime started — resuming instance {instance_id[:12]}…")

            job = rt.resume_process(instance_id)
            print(f"  resumed job {job.id[:12]}… step {_step_label(rt, job.id)}")
            assert job.state.get(WizardKeys.ANSWERS, {}).get("name") == "River"

            rt.provide_input(job.id, "yes")
            rt.provide_input(job.id, "yes")
            assert job.status == JobStatus.SUCCEEDED
            assert job.state.get(WizardKeys.COMMITTED) is True
            answers = rt.wizard_answers(job.id)
            print(f"  completed — answers: {answers}")
            print(f"  committed: {job.state.get(WizardKeys.COMMITTED)}")
        finally:
            rt.stop()

    _run_phase("1 · Register, submit, first input", phase_one)
    _run_phase("2 · Simulated restart + resume + commit", phase_two)

    storage.shutdown()
    print("\n✅ Full demo completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
