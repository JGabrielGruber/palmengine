"""0.63.34 — surface uses host packaging door; wizard CQRS continue gate."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from bundles.standard.app.host.application_host import ApplicationHost
from bundles.standard.app.settings import PalmSettings
from plugins.patterns.wizard.bindings.cqrs.commands import (
    ProvideWizardInputCommand,
    RequestWizardBacktrackCommand,
)
from plugins.patterns.wizard.bindings.cqrs.handlers import handle_wizard_command
from palm.system.log import reset_system_log_for_tests
from palm.system.structure.errors import AdmissionRefusedError
from palm.system.structure.inventory import GATED_PATHS, READINESS_EDGES, admission_inventory


def _settings() -> PalmSettings:
    return PalmSettings(
        load_example_definitions=True,
        storage_backend="memory",
        rebuild_projections_on_startup=False,
        reconcile_instances_on_startup=False,
    )


def test_host_resume_job_refused_when_assembly_skipped() -> None:
    reset_system_log_for_tests()
    host = ApplicationHost.for_mode("all_in_one", settings=_settings())
    host.start(structure_skip=True)
    try:
        assert host.admission.may_run_business is False
        with pytest.raises(AdmissionRefusedError):
            host.resume_job("job-missing")
    finally:
        host.shutdown()


def _closed_wizard_ctx() -> MagicMock:
    from palm.core.structure import AdmissionSnapshot, StructurePhase

    rt = MagicMock()
    rt.admission = AdmissionSnapshot(
        may_run_business=False,
        phase=StructurePhase.BLOCKED,
        reasons=("wizard_closed",),
    )
    ctx = MagicMock()
    ctx._router = None
    ctx._app = None
    ctx._runtime = rt
    return ctx


def test_wizard_provide_input_refused_when_runtime_closed() -> None:
    with pytest.raises(AdmissionRefusedError, match="wizard_closed"):
        handle_wizard_command(
            ProvideWizardInputCommand(instance_id="inst-1", value="x"),
            _closed_wizard_ctx(),
        )


def test_wizard_backtrack_refused_when_runtime_closed() -> None:
    with pytest.raises(AdmissionRefusedError, match="wizard_closed"):
        handle_wizard_command(
            RequestWizardBacktrackCommand(instance_id="inst-1"),
            _closed_wizard_ctx(),
        )


def test_inventory_surface_host_port() -> None:
    gated = {row["id"] for row in GATED_PATHS}
    assert "surface.host_port" in gated
    pretenders = {row["id"]: row["status"] for row in READINESS_EDGES}
    assert pretenders["surface.host_port_edge"] == "paid_0_63_34"
    assert admission_inventory()["gated_count"] >= 1
