"""Tests for agent skill path resolution."""

from __future__ import annotations

from pathlib import Path

from palm.runtimes.mcp.agent_assets import read_skill_asset, resolve_skill_root


def test_resolve_skill_root_finds_docs_copy() -> None:
    root = resolve_skill_root(None)
    assert root is not None
    assert (root / "SKILL.md").is_file()


def test_read_skill_asset_round_trip() -> None:
    root = resolve_skill_root(None)
    assert root is not None
    text = read_skill_asset(root, "references/mcp-patterns")
    assert "tool_description" in text


def test_resolve_skill_root_honors_override(tmp_path: Path) -> None:
    skill_dir = tmp_path / "palm"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("custom skill\n", encoding="utf-8")
    refs = skill_dir / "references"
    refs.mkdir()
    (refs / "agent-guide.md").write_text("custom guide\n", encoding="utf-8")

    root = resolve_skill_root(str(skill_dir))
    assert root == skill_dir
    assert read_skill_asset(root, "skill") == "custom skill\n"