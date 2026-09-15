"""0.68.16 — living README / transform-count / L0 continue copy."""

from __future__ import annotations

from pathlib import Path

from palm.common.transforms._apps import INSTALLED_TRANSFORMS
from palm.common.transforms.catalog import TRANSFORM_CATALOG

ROOT = Path(__file__).resolve().parents[2]
L0 = ROOT / "src/palm/runtimes/mcp/assist/tools.py"


def test_honest_transform_count_is_24() -> None:
    assert len(INSTALLED_TRANSFORMS) == 24
    assert set(TRANSFORM_CATALOG) == set(INSTALLED_TRANSFORMS)
    assert "parquet_load" not in INSTALLED_TRANSFORMS
    assert "parquet_load" not in TRANSFORM_CATALOG


def test_l0_continue_uses_instance_id_not_session() -> None:
    text = L0.read_text(encoding="utf-8")
    assert "{instance_id, flow_id, value}" in text
    assert '"instance_id": "inst-1"' in text
    assert "{session_id, flow_id, value}" not in text
    assert '"session_id": "inst-1"' not in text


def test_living_docs_match_status_and_real_cli() -> None:
    living = (
        "README.md",
        "ARCHITECTURE.md",
        "docs/llms.txt",
        "src/palm/runtimes/mcp/data/llms.txt",
        "website/llms.txt",
        "website/dist/llms.txt",
        "docs/wiki/guides/explorer-wizard.md",
        "examples/README.md",
    )
    for rel in living:
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert "No open minor" not in text
        assert "run_server(ServerRuntime())" not in text
        assert "palm resource list" not in text
        assert "palm resource invoke" not in text
        if rel in {
            "README.md",
            "ARCHITECTURE.md",
            "docs/llms.txt",
            "src/palm/runtimes/mcp/data/llms.txt",
            "website/llms.txt",
            "website/dist/llms.txt",
            "examples/README.md",
        }:
            assert "22 built-in" not in text
            assert "Built-in rules (22)" not in text
            assert "**22** built-in" not in text
