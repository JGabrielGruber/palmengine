"""0.67.4 — CapabilityRefusedError has honest surface voice (not generic RuntimeError)."""

from __future__ import annotations

from palm.core.structure import (
    CAPABILITY_WORK_DRAIN,
    AdmissionSnapshot,
    StructurePhase,
)
from bundles.standard.runtimes.cli.shared.admission_voice import format_cli_error
from bundles.standard.runtimes.mcp.rest_client import (
    PalmRestError,
    maybe_admission_refused_error,
)
from bundles.standard.runtimes.server.surfaces.rest import errors
from bundles.standard.runtimes.server.surfaces.ssr.explorer.admission_voice import operator_error_text
from palm.system.structure.errors import CapabilityRefusedError
from palm.system.structure.inventory import GATED_PATHS, READINESS_EDGES, admission_inventory


def _ready_without_drain() -> CapabilityRefusedError:
    snap = AdmissionSnapshot(
        may_run_business=True,
        phase=StructurePhase.READY,
        definition_id="local.embedded",
    )
    return CapabilityRefusedError(snap, CAPABILITY_WORK_DRAIN)


def test_rest_maps_capability_refused_not_500() -> None:
    """Ready without the organ is not submit_failed and not admission_refused."""
    exc = _ready_without_drain()
    resp = errors.maybe_admission_refused(exc)
    assert resp is not None
    assert resp.status == 409
    assert isinstance(resp.body, dict)
    assert resp.body["error"] == "capability_refused"
    assert "work_drain" in resp.body["detail"]
    assert resp.body["error"] != "admission_refused"


def test_rest_capability_helper_is_409() -> None:
    resp = errors.capability_refused("capability refused: 'work_drain' not installed")
    assert resp.status == 409
    assert resp.body["error"] == "capability_refused"


def test_rest_still_ignores_bare_runtime_error() -> None:
    assert errors.maybe_admission_refused(RuntimeError("other")) is None


def test_mcp_maps_capability_refused_not_500() -> None:
    mapped = maybe_admission_refused_error(_ready_without_drain())
    assert mapped is not None
    assert isinstance(mapped, PalmRestError)
    assert mapped.status == 409
    assert mapped.detail["error"] == "capability_refused"
    assert "work_drain" in mapped.detail["message"]


def test_cli_format_labels_capability_refused() -> None:
    text = format_cli_error(_ready_without_drain())
    assert "capability_refused" in text
    assert "work_drain" in text
    assert "admission_refused" not in text


def test_ssr_operator_error_labels_capability_refused() -> None:
    text = operator_error_text(_ready_without_drain())
    assert text.startswith("capability_refused:")
    assert "work_drain" in text


def test_websocket_maps_capability_not_internal() -> None:
    from bundles.standard.runtimes.server.surfaces.websocket.session import structure_refuse_voice

    payload = structure_refuse_voice("1", _ready_without_drain())
    assert payload is not None
    assert payload["op"] == "error"
    assert payload["error"]["code"] == "capability_refused"
    assert "work_drain" in payload["error"]["message"]


def test_inventory_capability_voice_paid() -> None:
    gated = {row["id"] for row in GATED_PATHS}
    assert "surface.capability_voice" in gated
    pretenders = {row["id"]: row["status"] for row in READINESS_EDGES}
    assert pretenders["surface.capability_voice_edge"] == "paid_0_67_4"
    assert admission_inventory()["gated_count"] >= 1
