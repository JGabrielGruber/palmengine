"""0.40.5 — Palm A analytics over Palm B system resources via remote_url."""

from __future__ import annotations

from examples.definitions.system import register_definitions as register_system
from palm.app.host.application_host import ApplicationHost
from palm.app.host.roles import HostProfile
from palm.app.settings import PalmSettings
from palm.definitions import FlowDefinition
from palm.runtimes.server.runtime import ServerRuntime


def test_analytics_system_flows_via_remote_url() -> None:
    """Host A queries palm-system-flows against ServerRuntime B (HTTP)."""
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
            # Local list may be empty; remote_url targets the other Palm
            q = host.analytics.query(
                "palm-system-flows",
                profile="table",
                params={"remote_url": remote.base_url},
            )
            assert q["status"] == "ok", q
            data = q.get("data") or {}
            cols = list(data.get("columns") or [])
            rows = list(data.get("rows") or [])
            assert q.get("meta", {}).get("row_count", 0) >= 1
            # table profile uses list-of-lists; resolve name column
            if "name" in cols:
                ni = cols.index("name")
                names = {str(r[ni]) for r in rows if isinstance(r, (list, tuple))}
            else:
                names = {str(r) for r in rows}
            assert "remote-dogfood-flow" in names, (names, cols, q)

            # Virtual view still works with remote source params
            per = host.analytics.query(
                "palm-system-instances-per-flow",
                profile="table",
                params={"remote_url": remote.base_url},
            )
            assert per["status"] == "ok", per
            assert per.get("meta", {}).get("virtual") is True
    finally:
        remote.stop()
