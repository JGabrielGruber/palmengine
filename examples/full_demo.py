#!/usr/bin/env python3
"""
End-to-end Palm demo — ApplicationHost, wizard input, commit, resume.

Run from the repository root::

    uv run python examples/full_demo.py
    # or: just demo-full

Demonstrates the **0.10 primary path**: ``ApplicationHost`` with CQRS command
dispatch, durable instance persistence, and simulated restart via a second host
session sharing the same ``StorageEngine``.
"""

from __future__ import annotations

import sys
from typing import Any

import palm.patterns
import palm.providers
import palm.storages.memory  # noqa: F401
from palm.app import ApplicationHost, DeploymentProfile, PalmSettings
from palm.app.bootstrap import runtime_start_options
from palm.core import StorageEngine
from palm.core.orchestration import JobStatus
from palm.definitions import FlowDefinition
from palm.patterns.wizard.bindings.compensation.handler import CommitResult, default_commit_registry
from palm.patterns.wizard.bindings.context.keys import WizardKeys


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


def _step_label(host: ApplicationHost, job_id: str) -> str:
    runtime = host.runtime()
    slug = runtime.current_wizard_step(job_id)
    return slug or runtime.get_job(job_id).status.value


def _run_phase(title: str, fn: Any) -> None:
    print(f"\n=== {title} ===")
    fn()


def main() -> int:
    storage = StorageEngine()
    storage.initialize(backend="memory")
    settings = PalmSettings(load_example_definitions=False)

    instance_id: str | None = None

    def phase_one() -> None:
        nonlocal instance_id
        host = ApplicationHost(settings, profile=DeploymentProfile.all_in_one(), storage=storage)
        host.start(**runtime_start_options(settings))
        try:
            _register_demo_flow(host.app.runtime().repository)
            print("Registered flow 'full-demo' with commit handler 'demo_commit'")
            print(f"Host runtimes: {host.running_runtimes()}")

            job = host.submit_flow("full-demo")
            instance_id = str(job.metadata.get("instance_id", job.id))
            print(f"Submitted job {job.id[:12]}… → instance {instance_id[:12]}…")
            print(f"  step: {_step_label(host, job.id)}")

            host.provide_input(job.id, "River")
            job = host.app.get_job(job.id)
            print(f"  after name: {_step_label(host, job.id)}")
            assert job.status == JobStatus.WAITING_FOR_INPUT

            views = host.list_instance_views(include_terminal=False)
            print(f"  projection index: {len(views)} active instance(s)")
            print("  persisted instance (simulating end of session)")
        finally:
            host.shutdown()

    def phase_two() -> None:
        nonlocal instance_id
        if not instance_id:
            raise RuntimeError("phase one did not produce an instance_id")

        host = ApplicationHost(settings, profile=DeploymentProfile.all_in_one(), storage=storage)
        host.start(**runtime_start_options(settings))
        try:
            _register_demo_flow(host.app.runtime().repository)
            print(f"New host started — resuming instance {instance_id[:12]}…")

            job = host.resume_process(instance_id)
            print(f"  resumed job {job.id[:12]}… step {_step_label(host, job.id)}")
            assert job.state.get(WizardKeys.ANSWERS, {}).get("name") == "River"

            host.provide_input(job.id, "yes")
            host.provide_input(job.id, "yes")
            job = host.app.get_job(job.id)
            assert job.status == JobStatus.SUCCEEDED
            assert job.state.get(WizardKeys.COMMITTED) is True
            answers = host.runtime().wizard_answers(job.id)
            print(f"  completed — answers: {answers}")
            print(f"  committed: {job.state.get(WizardKeys.COMMITTED)}")

            progress = host.get_wizard_progress(instance_id=instance_id)
            if progress is not None:
                print(f"  wizard progress: commit={progress.commit_status}")
        finally:
            host.shutdown()

    _run_phase("1 · Host start, submit, first input", phase_one)
    _run_phase("2 · Simulated restart + resume + commit", phase_two)

    storage.shutdown()
    print("\n✅ Full demo completed successfully.")
    print("   Next: palm status  (projection dashboard)  ·  palm doctor  (full health)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
