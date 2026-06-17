"""Explorer form schemas — :class:`~palm.core.context.state_schema.DictStateSchema` definitions."""

from __future__ import annotations

from palm.core.context.state_schema import DictStateSchema

_STRING = {"type": "string"}
_INTEGER = {"type": "integer", "minimum": 1, "maximum": 50}

FLOW_SUBMIT_FORM = DictStateSchema(
    {
        "type": "object",
        "properties": {
            "flow_name": _STRING,
            "wizard_name": _STRING,
            "wizard_steps": _INTEGER,
        },
    }
)