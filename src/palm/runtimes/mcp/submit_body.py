"""Shared submit body builders for MCP flow/wizard tools."""

from __future__ import annotations

from typing import Any


def submit_body(
    *,
    flow_name: str | None,
    wizard: dict[str, Any] | None,
    flow: dict[str, Any] | None,
    job_id: str | None,
    by_id: bool = False,
) -> dict[str, Any]:
    variants = sum(1 for value in (flow_name, wizard, flow) if value is not None)
    if variants != 1:
        raise ValueError("provide exactly one of flow_name, wizard, or flow")
    body: dict[str, Any] = {}
    if flow_name is not None:
        body["flow_name"] = flow_name
        if by_id:
            body["by_id"] = True
    elif wizard is not None:
        body["wizard"] = wizard
    else:
        body["flow"] = flow
    if job_id is not None:
        body["job_id"] = job_id
    return body


__all__ = ["submit_body"]
