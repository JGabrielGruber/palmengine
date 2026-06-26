"""Tests for compositional session status helper."""

from __future__ import annotations

from palm.common.operator.compose_status import build_compose_status


def test_build_compose_status_merges_tree_and_inspect() -> None:
    tree = {
        "instance_id": "inst-root",
        "root": {"instance_id": "inst-root", "flow": "main-menu", "step": "dispatch"},
        "focus": {"instance_id": "inst-root", "flow": "main-menu", "step": "dispatch"},
        "active_child": {
            "instance_id": "inst-child",
            "flow": "capture-knowledge",
            "status": "WAITING_FOR_INPUT",
        },
        "links": {"explorer": "http://localhost:8080/explorer/instances/inst-root"},
    }
    inspect = {
        "instance_id": "inst-root",
        "flow": "main-menu",
        "status": "WAITING_FOR_INPUT",
        "step": "dispatch",
        "step_kind": "resource",
        "answers_keys": ["goal", "menu_action"],
        "answers_preview": {"goal": "Compose docs"},
        "waiting_for_child": True,
        "child": {"instance_id": "inst-child", "status": "WAITING_FOR_INPUT"},
        "next_actions": ["resume_child_wait"],
        "operator_hint": "drive child inst-child",
        "collection_phase": "menu",
    }

    payload = build_compose_status(tree, inspect)

    assert payload["instance_id"] == "inst-root"
    assert payload["active_child"]["flow"] == "capture-knowledge"
    assert payload["answers_keys"] == ["goal", "menu_action"]
    assert payload["next_actions"] == ["resume_child_wait"]
    assert payload["operator_hint"] == "drive child inst-child"
    assert payload["collection_phase"] == "menu"
    assert payload["links"]["explorer"].endswith("inst-root")


def test_build_compose_status_includes_commit_result_summary() -> None:
    tree = {"instance_id": "inst-root", "root": {}, "focus": {}}
    inspect = {
        "instance_id": "inst-root",
        "flow": "knowkey_capture_knowledge_batch",
        "status": "SUCCEEDED",
        "committed": True,
        "result": {
            "main_node": {"id": "node-main", "title": "MCP Servers"},
            "captured_nodes": [{"id": "node-related"}],
        },
    }

    payload = build_compose_status(tree, inspect)

    assert payload["committed"] is True
    assert payload["result"]["main_node"]["id"] == "node-main"
    assert payload["result_summary"]["main_node_id"] == "node-main"
    assert payload["result_summary"]["node_ids"] == ["node-related"]