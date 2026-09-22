"""Product start ports — submit + able for the install board.

Takes seats, not the host bag. Session enrich is one path
(``enrich_reactive_start``). No hasattr forks.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from palm.core.structure import CAPABILITY_WORK_DRAIN, AdmissionSnapshot


def product_start_ports(
    *,
    execution: Any,
    session: Any | None,
    started: Callable[[], bool],
    admission: Callable[[], Any],
) -> tuple[Callable[..., Any], Callable[[], bool], Callable[[], bool]]:
    """Build ``submit`` / drain ``able`` / ready ``admission_able``.

    0.67.3 — work-plane able is ``started ∧ ready ∧ work_drain``.
    Wait stays ready-only (``started ∧ may_run_business``).
    """

    def submit(flow_id: str, payload: dict[str, Any]) -> Any:
        body = dict(payload or {})
        seed = body.pop("_seed_state", None)
        submit_body: dict[str, Any] = {"flow_name": flow_id, "metadata": body}
        if seed is not None:
            submit_body["state"] = seed
        if session is not None:
            origin = session.reactive_origin(flow_id, body)
            submit_body = session.enrich_reactive_start(
                submit_body,
                origin=origin,
                surface="work-drain",
            )
        if execution is None:
            raise RuntimeError("host execution not bound")
        return execution.flows.submit_flow_body(submit_body)

    def _snap() -> AdmissionSnapshot | None:
        snap = admission()
        return snap if isinstance(snap, AdmissionSnapshot) else None

    def admission_able() -> bool:
        if not started():
            return False
        snap = _snap()
        return bool(snap is not None and snap.may_run_business)

    def able() -> bool:
        if not admission_able():
            return False
        snap = _snap()
        return bool(snap is not None and snap.has_capability(CAPABILITY_WORK_DRAIN))

    return submit, able, admission_able
