"""Architectural boundary tests for ``palm.system`` (0.57.2+)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

FORBIDDEN_PREFIXES = (
    "palm.services",
    "bundles.standard.runtimes",
    "plugins.patterns",
    "bundles.standard.app",
)


def _system_root() -> Path:
    return Path(__file__).resolve().parents[1] / "src" / "palm" / "system"


def _is_forbidden(module: str | None) -> bool:
    if not module:
        return False
    for prefix in FORBIDDEN_PREFIXES:
        if module == prefix or module.startswith(prefix + "."):
            return True
    return False


def test_system_package_exists() -> None:
    root = _system_root()
    assert root.is_dir(), "palm.system package must exist"
    assert (root / "__init__.py").is_file()
    assert (root / "instance.py").is_file()
    assert (root / "interfaces" / "execution.py").is_file()


def test_system_has_no_product_surface_pattern_imports() -> None:
    """palm.system must not import services, runtimes surfaces, patterns, or app."""
    root = _system_root()
    violations: list[str] = []

    for path in sorted(root.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        rel = path.relative_to(root.parents[1])
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if _is_forbidden(node.module):
                    violations.append(f"{rel}: from {node.module}")
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if _is_forbidden(alias.name):
                        violations.append(f"{rel}: import {alias.name}")

    assert not violations, "forbidden imports in palm.system:\n" + "\n".join(violations)


def test_public_exports() -> None:
    from palm.system import ExecutionPort, SystemInstance

    assert ExecutionPort is not None
    assert SystemInstance is not None


def test_base_runtime_is_system_instance_and_execution_port() -> None:
    from palm.system import BaseRuntime, ExecutionPort, SystemInstance
    from palm.system.runtime.base import BaseRuntime as CanonicalBaseRuntime

    assert BaseRuntime is CanonicalBaseRuntime
    runtime = BaseRuntime()
    assert isinstance(runtime, SystemInstance)
    assert isinstance(runtime, ExecutionPort)
    assert runtime.execution is runtime


def test_execution_port_fake_is_usable() -> None:
    """Test doubles can implement ExecutionPort without a full host."""
    from palm.system import ExecutionPort

    class FakePort:
        def invoke_resource(self, resource_ref: str | None = None, **kwargs: object) -> dict:
            return {"ref": resource_ref, "ok": True}

        def start_workload(self, spec: object, **kwargs: object) -> dict:
            return {"spec": spec, "status": "pending"}

        def exec_workload(
            self, workload_id: str, command: list[str] | tuple[str, ...], **kwargs: object
        ) -> dict:
            return {"id": workload_id, "command": list(command)}

        def stop_workload(self, workload_id: str, **kwargs: object) -> dict:
            return {"id": workload_id, "status": "stopped"}

        def workload_status(self, workload_id: str, *, refresh: bool = False) -> dict:
            return {"id": workload_id, "refresh": refresh}

        def resume_job(self, job_id: str) -> None:
            return None

        def list_jobs(self, status: object = None) -> list:
            return []

        def list_workloads(self, **kwargs: object) -> list:
            return []

        def list_workload_runtimes(self) -> list:
            return []

        def doctor_workloads(self) -> dict:
            return {}

        def stop_owned_workloads(self, **kwargs: object) -> list:
            return []

    fake = FakePort()
    assert isinstance(fake, ExecutionPort)
    assert fake.invoke_resource("kv://x")["ok"] is True


def test_port_bridges_to_core_protocols() -> None:
    """ExecutionPort adapters satisfy ResourceInvoker / WorkloadDriver for graphs."""
    from palm.core.resource.invoker import ResourceInvoker
    from palm.core.resource.result import ProviderResult
    from palm.core.workload.driver import WorkloadDriver
    from palm.system.effects import resource_invoker_from_port, workload_driver_from_port

    class FakePort:
        def invoke_resource(self, resource_ref: str | None = None, **kwargs: object) -> ProviderResult:
            return ProviderResult.ok({"ref": resource_ref})

        def start_workload(self, spec: object, **kwargs: object) -> object:
            raise NotImplementedError

        def exec_workload(self, workload_id: str, command: object, **kwargs: object) -> object:
            raise NotImplementedError

        def stop_workload(self, workload_id: str, **kwargs: object) -> object:
            raise NotImplementedError

        def workload_status(self, workload_id: str, *, refresh: bool = False) -> object:
            raise NotImplementedError

        def resume_job(self, job_id: str) -> object:
            raise NotImplementedError

        def list_jobs(self, status: object = None) -> list:
            return []

        def list_workloads(self, **kwargs: object) -> list:
            return []

        def list_workload_runtimes(self) -> list:
            return []

        def doctor_workloads(self) -> dict:
            return {}

        def stop_owned_workloads(self, **kwargs: object) -> list:
            return []

    port = FakePort()
    invoker = resource_invoker_from_port(port)
    assert isinstance(invoker, ResourceInvoker)
    assert invoker.invoke("x").success is True
    # driver construction does not require live workloads
    driver = workload_driver_from_port(port)
    assert isinstance(driver, WorkloadDriver)


def test_resolve_effects_prefers_execution_port() -> None:
    from palm.common.patterns.build_context import PatternBuildContext
    from palm.common.patterns.effects import resolve_resource_invoker
    from palm.core.resource.result import ProviderResult
    from palm.system.effects import PortResourceInvoker

    class FakePort:
        def invoke_resource(self, resource_ref: str | None = None, **kwargs: object) -> ProviderResult:
            return ProviderResult.ok({"via": "port", "ref": resource_ref})

        def start_workload(self, spec: object, **kwargs: object) -> object:
            raise NotImplementedError

        def exec_workload(self, workload_id: str, command: object, **kwargs: object) -> object:
            raise NotImplementedError

        def stop_workload(self, workload_id: str, **kwargs: object) -> object:
            raise NotImplementedError

        def workload_status(self, workload_id: str, *, refresh: bool = False) -> object:
            raise NotImplementedError

        def resume_job(self, job_id: str) -> object:
            raise NotImplementedError

        def list_jobs(self, status: object = None) -> list:
            return []

        def list_workloads(self, **kwargs: object) -> list:
            return []

        def list_workload_runtimes(self) -> list:
            return []

        def doctor_workloads(self) -> dict:
            return {}

        def stop_owned_workloads(self, **kwargs: object) -> list:
            return []

    class EngineStub:
        is_initialized = True

        def initialize(self) -> None:
            return None

        def invoke(self, *a: object, **k: object) -> ProviderResult:
            return ProviderResult.ok({"via": "engine"})

    ctx = PatternBuildContext(execution=FakePort(), resource_engine=EngineStub())  # type: ignore[arg-type]
    invoker = resolve_resource_invoker(ctx)
    assert isinstance(invoker, PortResourceInvoker)
    assert invoker.invoke("r").data["via"] == "port"


@pytest.mark.parametrize(
    "name",
    [
        "invoke_resource",
        "start_workload",
        "exec_workload",
        "stop_workload",
        "workload_status",
        "resume_job",
        "list_jobs",
        "list_workloads",
        "list_workload_runtimes",
        "doctor_workloads",
        "stop_owned_workloads",
    ],
)
def test_execution_port_protocol_names(name: str) -> None:
    from palm.system.interfaces.execution import ExecutionPort

    assert hasattr(ExecutionPort, name)
