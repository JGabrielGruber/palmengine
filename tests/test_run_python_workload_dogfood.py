"""run-python dogfood — Workload step on host (and Spec sugar)."""

from __future__ import annotations

from bundles.standard.app import ApplicationHost, DeploymentProfile
from bundles.standard.app.settings import PalmSettings
from palm.system.subsystems.planes.workload.run_python import build_run_python_spec, resolve_runtime_choice
from palm.core.behavior_tree import PatternStatus
from palm.core.workload import IsolationPolicy, WorkloadKind
from plugins.patterns.wizard.bindings.definitions.config import WizardConfig, WizardStepConfig
from plugins.patterns.wizard.pattern import WizardPattern
from palm.states import BlackboardState


def test_build_run_python_spec_local() -> None:
    spec = build_run_python_spec(code="print(1)", runtime="local")
    assert spec.kind is WorkloadKind.RUN
    assert spec.placement.runtime == "local"
    assert spec.isolation is IsolationPolicy.BEST_EFFORT
    assert spec.command[-1] == "print(1)"


def test_build_run_python_spec_host() -> None:
    spec = build_run_python_spec(code="print(1)", runtime="host")
    assert spec.kind is WorkloadKind.RUN
    assert spec.placement.runtime == "host"
    assert spec.isolation is IsolationPolicy.HOST
    assert spec.command[-1] == "print(1)"


def test_build_run_python_spec_neonroot() -> None:
    spec = build_run_python_spec(code="print(2)", runtime="neonroot", image="palm-ci")
    assert spec.placement.runtime == "neonroot"
    assert spec.isolation is IsolationPolicy.HERMETIC
    assert spec.image == "palm-ci"
    assert spec.seed == {"type": "none"}


def test_resolve_runtime_auto_prefers_string() -> None:
    assert resolve_runtime_choice("local") == "local"
    assert resolve_runtime_choice("host") == "host"
    assert resolve_runtime_choice("neonroot") == "neonroot"
    assert resolve_runtime_choice("auto") in ("local", "neonroot")


def test_wizard_workload_step_host_run() -> None:
    from palm.core.workload import WorkloadEngine
    from plugins.runners.host.runtime import HostWorkloadRuntime

    engine = WorkloadEngine()
    engine.initialize(runtimes={"host": HostWorkloadRuntime(enabled=True)})

    config = WizardConfig(
        steps=(
            WizardStepConfig(
                slug="code",
                title="Code",
                prompt="code?",
            ),
            WizardStepConfig(
                slug="run",
                title="Run",
                prompt="run",
                step_kind="workload",
                output_key="run_result",
                params={
                    "code": "{{ state.code }}",
                    "runtime": "host",
                },
            ),
        ),
        include_summary=False,
        include_commit=False,
    )
    wizard = WizardPattern(
        name="run-py-test",
        config=config,
        workload_engine=engine,
    )
    state = BlackboardState()
    assert wizard.tick(state) == PatternStatus.WAITING_FOR_INPUT
    wizard.provide_input(state, "print('dogfood')")
    # may take one or two ticks (workload RUNNING then SUCCESS)
    status = wizard.tick(state)
    for _ in range(5):
        if status in (PatternStatus.SUCCESS, PatternStatus.FAILURE):
            break
        status = wizard.tick(state)
    assert status == PatternStatus.SUCCESS
    assert "dogfood" in str(state.get("stdout") or "")
    assert state.get("exit_code") == 0
    engine.shutdown()


def test_run_python_flow_registers_and_runs_on_host() -> None:
    settings = PalmSettings.for_tests(load_examples=True)
    settings.workload_host_enabled = True
    host = ApplicationHost(settings=settings, profile=DeploymentProfile.all_in_one())
    host.start()
    try:
        flows = host.definitions.list_flows()
        names = {
            (f.get("name") if isinstance(f, dict) else getattr(f, "name", None))
            for f in flows
        }
        assert "run-python" in names
        assert "hermetic-run-code" in names

        from palm.core.orchestration import JobStatus

        rt = host._app.runtime()
        job = rt.submit_flow("run-python")
        jid = job.id
        assert job.status == JobStatus.WAITING_FOR_INPUT
        rt.provide_input(jid, "host")
        job = rt.get_job(jid)
        assert job.status == JobStatus.WAITING_FOR_INPUT
        rt.provide_input(jid, "print(40+2)")
        job = rt.get_job(jid)
        for _ in range(20):
            job = rt.get_job(jid)
            if job.status in (JobStatus.SUCCEEDED, JobStatus.FAILED):
                break
            if job.status == JobStatus.WAITING_FOR_INPUT:
                rt.provide_input(jid, "ok")
            elif hasattr(rt, "drive"):
                rt.drive(jid)
            else:
                rt.orchestration.drive(jid)
        job = rt.get_job(jid)
        assert job.status == JobStatus.SUCCEEDED
        state = job.state
        assert state is not None
        assert state.get("exit_code") == 0
        assert "42" in str(state.get("stdout") or "")
    finally:
        host.shutdown()
