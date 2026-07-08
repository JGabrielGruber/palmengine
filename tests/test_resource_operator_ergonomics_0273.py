"""0.27.3 — resource operator ergonomics (doctor preflight, failure modes, remediation)."""

from __future__ import annotations

import pytest

import palm.providers  # noqa: F401 — register providers
from palm.common import DefinitionRepository
from palm.common.operator.compact import compact_wizard_inspect
from palm.common.operator.resource_remediation import (
    enrich_provider_result,
    resource_invoke_remediation,
)
from palm.common.resource import resource_definition_resolver
from examples.definitions.coconut_resources import LOAD_COCONUT_PLAYER
from palm.common.resource.preflight import (
    build_resource_preflight,
    resource_preflight_issues,
    rest_resource_has_base_url,
)
from palm.common.runtimes.server.diagnostics import build_doctor_report
from palm.core.behavior_tree import PatternStatus
from palm.core.resource import ResourceEngine
from palm.definitions import FlowDefinition, ResourceDefinition
from palm.patterns.wizard.bindings.behavior_tree.tree import build_wizard_tree
from palm.patterns.wizard.bindings.context.keys import WizardKeys
from palm.patterns.wizard.bindings.definitions.config import WizardConfig, WizardStepConfig
from palm.runtimes.embedded import EmbeddedRuntime
from palm.services.execution.providers.service import ProviderExecutionService
from palm.states import BlackboardState


def _check_health_resource(*, base_url: str | None = None) -> ResourceDefinition:
    params = {"base_url": base_url} if base_url else {}
    return ResourceDefinition(
        id="resource-check-health",
        name="check-health",
        provider="rest",
        action="fetch",
        resource_id="health/check",
        params=params,
    )


def test_rest_resource_has_base_url_detects_absolute_resource_id() -> None:
    resource = ResourceDefinition(
        name="remote",
        provider="rest",
        resource_id="https://api.example/health",
    )
    assert rest_resource_has_base_url(resource) is True


def test_rest_resource_has_base_url_rejects_template_base_url() -> None:
    resource = ResourceDefinition(
        name="remote",
        provider="rest",
        resource_id="health/check",
        params={"base_url": "{{ state.api_url }}"},
    )
    assert rest_resource_has_base_url(resource) is False


def test_doctor_report_flags_rest_resources_missing_base_url() -> None:
    runtime = EmbeddedRuntime()
    runtime.start()
    try:
        runtime.repository.register_resource(_check_health_resource())
        report = build_doctor_report(runtime)
        assert report["status"] == "degraded"
        assert any("missing base_url" in issue for issue in report["issues"])
        preflight = report["resource_preflight"]
        assert preflight["rest_missing_base_url_count"] == 1
        assert preflight["rest_missing_base_url"][0]["name"] == "check-health"
        assert preflight["check_health"]["skipped"] is True
    finally:
        runtime.stop()


def test_doctor_probe_check_health_passes(rest_base_url: str) -> None:
    runtime = EmbeddedRuntime()
    runtime.start()
    try:
        runtime.repository.register_resource(_check_health_resource(base_url=rest_base_url))
        report = build_doctor_report(runtime)
        probe = report["resource_preflight"]["check_health"]
        assert probe["available"] is True
        assert probe["success"] is True
        assert report["status"] == "ok"
    finally:
        runtime.stop()


def test_resource_invoke_remediation_for_missing_base_url() -> None:
    hint = resource_invoke_remediation(
        error="rest fetch requires base_url param or absolute resource_id URL",
        resource_ref="check-health",
        provider="rest",
    )
    assert hint is not None
    assert "base_url" in hint
    assert "check-health" in hint


def test_enrich_provider_result_adds_remediation() -> None:
    enriched = enrich_provider_result(
        {
            "success": False,
            "error": "rest fetch requires base_url param or absolute resource_id URL",
            "metadata": {"provider": "rest", "resource_ref": "check-health"},
        }
    )
    assert "remediation" in enriched


def test_provider_execution_service_returns_remediation() -> None:
    runtime = EmbeddedRuntime()
    runtime.start()
    try:
        runtime.repository.register_resource(_check_health_resource())
        service = ProviderExecutionService(
            commands=None,
            queries=None,
            schemas=None,
            runtime=runtime,
        )
        result = service.invoke("check-health")
        assert result["success"] is False
        assert "remediation" in result
    finally:
        runtime.stop()


def _resource_wizard_config(
    *,
    on_resource_failure: str = "block",
    branch_target: str | None = None,
) -> WizardConfig:
    params: dict[str, object] = {"on_resource_failure": on_resource_failure}
    if branch_target:
        params["on_resource_failure_branch"] = branch_target
    return WizardConfig(
        steps=(
            WizardStepConfig(
                slug="preflight",
                title="Preflight",
                prompt="Check health",
                step_kind="resource",
                resource_ref="check-health",
                output_key="health",
                params=params,
            ),
            WizardStepConfig(slug="fallback", title="Fallback", prompt="Fallback path"),
            WizardStepConfig(slug="done", title="Done", prompt="Finish"),
        ),
        include_summary=False,
    )


def _resource_engine_with_check_health() -> tuple[ResourceEngine, DefinitionRepository]:
    repo = DefinitionRepository()
    repo.register_resource(_check_health_resource())
    engine = ResourceEngine()
    engine.initialize(definition_resolver=resource_definition_resolver(repo))
    return engine, repo


def test_resource_step_block_on_failure() -> None:
    engine, _repo = _resource_engine_with_check_health()
    config = _resource_wizard_config(on_resource_failure="block")
    root, _sequence = build_wizard_tree("demo", config, resource_engine=engine)
    state = BlackboardState()
    assert root.tick(state) == PatternStatus.FAILURE
    engine.shutdown()


def test_resource_step_skip_on_failure() -> None:
    engine, _repo = _resource_engine_with_check_health()
    config = _resource_wizard_config(on_resource_failure="skip")
    root, _sequence = build_wizard_tree("demo", config, resource_engine=engine)
    state = BlackboardState()
    assert root.tick(state) == PatternStatus.WAITING_FOR_INPUT
    assert state.get(WizardKeys.CURRENT_STEP) == "fallback"
    answers = state.get(WizardKeys.ANSWERS) or {}
    assert answers.get("health") is None
    engine.shutdown()


def test_resource_step_branch_on_failure() -> None:
    engine, _repo = _resource_engine_with_check_health()
    config = _resource_wizard_config(
        on_resource_failure="branch",
        branch_target="fallback",
    )
    root, _sequence = build_wizard_tree("demo", config, resource_engine=engine)
    state = BlackboardState()
    assert root.tick(state) == PatternStatus.WAITING_FOR_INPUT
    assert state.get(WizardKeys.CURRENT_STEP) == "fallback"
    engine.shutdown()


def test_resource_step_branch_requires_target() -> None:
    engine, _repo = _resource_engine_with_check_health()
    config = _resource_wizard_config(on_resource_failure="branch")
    root, _sequence = build_wizard_tree("demo", config, resource_engine=engine)
    state = BlackboardState()
    assert root.tick(state) == PatternStatus.FAILURE
    engine.shutdown()


def test_kv_preflight_reports_backend_and_namespaces() -> None:
    runtime = EmbeddedRuntime()
    runtime.start()
    try:
        runtime.repository.register_resource(LOAD_COCONUT_PLAYER)
        preflight = build_resource_preflight(runtime)
        kv = preflight["kv"]
        assert kv["resource_count"] == 1
        assert kv["backend_resolved"] in {"memory", "storage"}
        assert kv["namespaces"] == ["coconut"]
        report = build_doctor_report(runtime)
        assert report["resource_preflight"]["kv"]["resource_count"] == 1
    finally:
        runtime.stop()


def test_file_preflight_flags_non_writable_root(tmp_path, monkeypatch) -> None:
    blocked_root = tmp_path / "blocked"
    blocked_root.mkdir()
    blocked_root.chmod(0o555)
    runtime = EmbeddedRuntime()
    runtime.start()
    try:
        monkeypatch.setattr(
            "palm.common.resource.preflight.resolve_documents_root",
            lambda _runtime: blocked_root,
        )
        runtime.repository.register_resource(
            ResourceDefinition(
                name="read-doc",
                provider="file",
                action="read",
                resource_id="notes/demo.json",
                params={"format": "json"},
            )
        )
        preflight = build_resource_preflight(runtime)
        assert preflight["file"]["resource_count"] == 1
        assert preflight["file"]["writable"] is False
        issues = resource_preflight_issues(preflight)
        assert any("documents_root is not writable" in row for row in issues)
        report = build_doctor_report(runtime)
        assert report["status"] == "degraded"
        assert any("documents_root is not writable" in row for row in report["issues"])
    finally:
        blocked_root.chmod(0o755)
        runtime.stop()


def test_compact_inspect_surfaces_resource_remediation() -> None:
    payload = compact_wizard_inspect(
        {
            "instance_id": "inst-1",
            "status": "WAITING_FOR_INPUT",
            "current_step_slug": "preflight",
            "prompt": {
                "step": "preflight",
                "step_kind": "resource",
                "field_type": "resource",
                "resource_error": "rest fetch requires base_url",
                "resource_remediation": "Set base_url in params",
            },
        }
    )
    assert payload["resource_error"] == "rest fetch requires base_url"
    assert payload["resource_remediation"] == "Set base_url in params"
    assert payload["operator_hint"] == "Set base_url in params"