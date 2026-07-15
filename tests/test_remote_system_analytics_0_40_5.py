"""0.40.5+ — Palm A analytics over Palm B via **origin ResourceDefinitions**."""

from __future__ import annotations

from examples.definitions.system import register_definitions as register_system
from examples.definitions.system.origin_dashboard import register_origin_system_dashboard
from examples.definitions.system.origin_resources import (
    register_origin_system_resources,
)
from palm.app.host.application_host import ApplicationHost
from palm.app.host.roles import HostProfile
from palm.app.settings import PalmSettings
from palm.definitions import FlowDefinition
from palm.runtimes.server.runtime import ServerRuntime


def test_analytics_origin_resources_not_query_params() -> None:
    """Origin remote_url lives on the resource; analytics only names the dataset."""
    remote = ServerRuntime(host="127.0.0.1", port=0)
    remote.start(port=0)
    remote.repository.save_flow(
        FlowDefinition(
            id="flow-remote-dogfood",
            name="remote-dogfood-flow",
            pattern="pipeline",
            options={"steps": []},
        )
    )
    try:
        with ApplicationHost(
            settings=PalmSettings.for_tests(load_examples=False),
            profile=HostProfile.all_in_one(),
        ) as host:
            register_system(host.app.repository())
            names = register_origin_system_resources(
                host.app.repository(),
                remote.base_url,
                name_prefix="origin",
            )
            assert "origin-system-flows" in names
            register_origin_system_dashboard(
                name_prefix="origin",
                remote_url=remote.base_url,
            )

            # No params — definition carries remote_url
            q = host.analytics.query("origin-system-flows", profile="table")
            assert q["status"] == "ok", q
            data = q.get("data") or {}
            cols = list(data.get("columns") or [])
            rows = list(data.get("rows") or [])
            assert q.get("meta", {}).get("row_count", 0) >= 1
            if "name" in cols:
                ni = cols.index("name")
                found = {str(r[ni]) for r in rows if isinstance(r, list | tuple)}
            else:
                found = {str(r) for r in rows}
            assert "remote-dogfood-flow" in found, (found, cols, q)

            # Local dataset does not magically include remote flow
            local = host.analytics.query("palm-system-flows", profile="table")
            assert local["status"] == "ok", local

            per = host.analytics.query(
                "origin-system-instances-per-flow",
                profile="table",
            )
            assert per["status"] == "ok", per
            assert per.get("meta", {}).get("virtual") is True

            rendered = host.analytics.render_dashboard("origin-system")
            assert rendered.get("status") == "ok", rendered
            dash = rendered.get("dashboard") or {}
            assert dash.get("name") == "origin-system", rendered
    finally:
        remote.stop()
