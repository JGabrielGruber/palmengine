"""Palm provider system-read actions + analytics datasets."""

from __future__ import annotations

from examples.definitions.system import register_definitions as register_system
from palm.app.host.application_host import ApplicationHost
from palm.app.host.roles import DeploymentProfile
from palm.app.settings import PalmSettings
from palm.providers.palm.bindings.resource.system_inspect import (
    SYSTEM_READ_ACTIONS,
    is_system_read_action,
)


def test_system_read_action_names() -> None:
    assert is_system_read_action("list_jobs")
    assert is_system_read_action("list_instances")
    assert not is_system_read_action("submit_flow")
    assert "list_flows" in SYSTEM_READ_ACTIONS


def test_local_list_flows_and_analytics() -> None:
    with ApplicationHost(
        settings=PalmSettings.for_tests(load_examples=True),
        profile=DeploymentProfile.all_in_one(),
    ) as host:
        register_system(host.app.repository())
        body = host.execution.providers.invoke("palm-system-flows", action="list_flows")
        # resource def may force action from definition — invoke by name
        body = host.execution.providers.invoke("palm-system-flows")
        assert body.get("success") is True, body
        data = body.get("data") or {}
        assert "items" in data
        assert data.get("count", 0) >= 1

        q = host.analytics.query("palm-system-flows", profile="table")
        assert q["status"] == "ok", q
        assert q["meta"]["row_count"] is None or q["meta"]["row_count"] >= 0
        assert "columns" in q["data"]

        names = {d["dataset"] for d in host.analytics.list_datasets()}
        assert "palm-system-jobs" in names
        assert "palm-system-instances" in names

        per_flow = host.analytics.query(
            "palm-system-instances-per-flow", profile="table"
        )
        assert per_flow["status"] == "ok", per_flow
        assert per_flow["meta"].get("virtual") is True

        dash = host.analytics.render_dashboard("palm-system")
        assert dash["status"] == "ok", dash
        assert len(dash["tiles"]) >= 4
