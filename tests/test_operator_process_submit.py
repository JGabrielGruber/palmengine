"""Tests for interactive process submit guards."""

from __future__ import annotations

import pytest

from palm.common.operator.process_submit import (
    process_submit_hints,
    validate_process_submit,
)


def test_validate_process_submit_rejects_catalog_without_all_flows() -> None:
    process = {
        "name": "knowkey_compose",
        "flows": [{}, {}, {}],
        "metadata": {
            "entry_flow": "knowkey_main_menu",
            "mcp": {
                "entries": {
                    "fast": {
                        "flow": "knowkey_capture_knowledge_batch",
                        "submit": (
                            'palm_submit_wizard(flow_name="knowkey_capture_knowledge_batch")'
                        ),
                    }
                }
            },
        },
    }

    with pytest.raises(ValueError, match="interactive catalog"):
        validate_process_submit(process)

    validate_process_submit(process, mode="all_flows")


def test_process_submit_hints_includes_fast_entry() -> None:
    process = {
        "metadata": {
            "mcp": {
                "entries": {
                    "fast": {
                        "flow": "knowkey_capture_knowledge_batch",
                        "submit": (
                            'palm_submit_wizard(flow_name="knowkey_capture_knowledge_batch")'
                        ),
                    }
                }
            }
        }
    }

    hints = process_submit_hints(process)

    assert any("knowkey_capture_knowledge_batch" in hint for hint in hints)
