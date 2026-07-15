"""0.45.1 — work drain seeds pipeline state from inbound."""

from __future__ import annotations

from palm.app import ApplicationHost, PalmSettings
from palm.definitions import FlowDefinition, ResourceDefinition


def test_inbound_webhook_seeds_pipeline_state() -> None:
    settings = PalmSettings.for_tests(load_examples=False)
    host = ApplicationHost(settings=settings)
    host.start()
    try:
        repo = host.app.repository()
        repo.save_flow(
            FlowDefinition(
                name="seed-check",
                pattern="pipeline",
                options={
                    "steps": [
                        {
                            "name": "copy_type",
                            "source_key": "event",
                            "target_key": "event_type",
                            "rule": "jsonpath_extract",
                            "options": {"path": "type"},
                        }
                    ]
                },
            )
        )
        repo.save_resource(
            ResourceDefinition(
                name="wh-seed",
                provider="kv",
                action="put",
                resource_id="inbound/seed",
                params={},
                metadata={
                    "inbound": {
                        "enabled": True,
                        "mode": "webhook",
                        "work": {
                            "flow_id": "seed-check",
                            "seed_state": {"event": "inbound.payload"},
                        },
                    }
                },
            )
        )
        host.reload_inbound_bindings()
        host.inbound.handle_webhook(
            "wh-seed",
            body={"id": "evt-1", "type": "resource.changed"},
            headers={},
        )
        host.work_drain.tick(limit=1)
        host._execution.flows.wait_until_idle(timeout=5.0)

        instances = host.system.list_instances(limit=5)
        rows = instances if isinstance(instances, list) else instances.get("items", [])
        assert rows
        job_id = rows[-1]["job_id"]
        job = host.app.runtime().get_job(job_id)
        assert job.state.get("event_type") == "resource.changed"
        assert job.state.get("event", {}).get("id") == "evt-1"

        meta = host._execution.flows.get_instance_metadata(rows[-1]["instance_id"])
        assert meta.get("inbound", {}).get("payload", {}).get("id") == "evt-1"
    finally:
        host.shutdown()