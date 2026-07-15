"""Thin reaction flows for inbound signals (definition-only)."""

from __future__ import annotations

from palm.definitions import FlowDefinition

ON_INBOUND_WEBHOOK = FlowDefinition(
    id="flow-on-inbound-webhook",
    name="on-inbound-webhook",
    pattern="wizard",
    options={
        "title": "Inbound signal received",
        "description": "Dogfood reaction for inbound-webhook-demo / origin stream",
        "steps": [
            {
                "slug": "ack",
                "kind": "introduction",
                "title": "Inbound",
                "prompt": (
                    "An inbound resource signal was accepted and this flow was "
                    "started via WorkIntent (run-when-able)."
                ),
            },
        ],
    },
)

__all__ = ["ON_INBOUND_WEBHOOK"]
