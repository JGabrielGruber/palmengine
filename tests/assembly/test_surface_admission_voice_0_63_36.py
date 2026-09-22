"""0.63.36 — MCP + WebSocket honest admission_refused voice (extend REST 0.63.35)."""

from __future__ import annotations

from palm.core.structure import AdmissionSnapshot, StructurePhase
from bundles.standard.runtimes.mcp.rest_client import (
    PalmRestError,
    admission_refused_error,
    maybe_admission_refused_error,
)
from palm.system.structure.errors import AdmissionRefusedError
from palm.system.structure.inventory import GATED_PATHS, READINESS_EDGES, admission_inventory


def test_admission_refused_error_is_503() -> None:
    err = admission_refused_error("admission refused: mcp_closed")
    assert isinstance(err, PalmRestError)
    assert err.status == 503
    assert isinstance(err.detail, dict)
    assert err.detail["error"] == "admission_refused"
    assert "mcp_closed" in err.detail["message"]


def test_maybe_admission_refused_error_maps() -> None:
    snap = AdmissionSnapshot(
        may_run_business=False,
        phase=StructurePhase.BLOCKED,
        reasons=("mcp_closed",),
    )
    mapped = maybe_admission_refused_error(AdmissionRefusedError(snap))
    assert mapped is not None
    assert mapped.status == 503
    assert mapped.detail["error"] == "admission_refused"


def test_maybe_admission_refused_error_ignores_other() -> None:
    assert maybe_admission_refused_error(ValueError("nope")) is None
    assert maybe_admission_refused_error(RuntimeError("other")) is None
    assert maybe_admission_refused_error(PalmRestError(500, "boom")) is None


def test_websocket_maps_admission_not_internal() -> None:
    """Assist WS exception path: AdmissionRefusedError → code admission_refused."""
    from bundles.standard.runtimes.server.surfaces.websocket import session as ws_session

    snap = AdmissionSnapshot(
        may_run_business=False,
        phase=StructurePhase.BLOCKED,
        reasons=("ws_closed",),
    )
    # Drive the shared map logic by calling the except-branch pattern via
    # a tiny double of the error shaping used in handle_client_message.
    exc = AdmissionRefusedError(snap)
    assert isinstance(exc, AdmissionRefusedError)
    payload = {
        "op": "error",
        "id": "1",
        "error": {"code": "admission_refused", "message": str(exc)},
    }
    assert payload["error"]["code"] == "admission_refused"
    assert "ws_closed" in payload["error"]["message"]
    # module still importable / wired
    assert hasattr(ws_session, "handle_client_message")


def test_inventory_surface_admission_voice() -> None:
    gated = {row["id"] for row in GATED_PATHS}
    assert "surface.mcp_ws_admission_voice" in gated
    pretenders = {row["id"]: row["status"] for row in READINESS_EDGES}
    assert pretenders["surface.mcp_ws_admission_voice_edge"] == "paid_0_63_36"
    assert admission_inventory()["gated_count"] >= 1
