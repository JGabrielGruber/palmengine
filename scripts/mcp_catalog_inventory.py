#!/usr/bin/env python3
"""Inventory Palm MCP tools for a surface — size proxy for token efficiency (0.31.1).

Usage::

    uv run --extra mcp python scripts/mcp_catalog_inventory.py
    uv run --extra mcp python scripts/mcp_catalog_inventory.py --surface assist
    uv run --extra mcp python scripts/mcp_catalog_inventory.py --surface full --json

Token estimate is chars/4 (relative proxy, not a model tokenizer).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

# repo root on path
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT / "src"))


def _est_tokens(text: str) -> int:
    return max(1, (len(text) + 3) // 4)


def _jdump(obj: Any) -> str:
    return json.dumps(
        obj,
        separators=(",", ":"),
        default=lambda x: list(x) if isinstance(x, set) else str(x),
    )


async def _list_tool_rows(surface: str) -> list[dict[str, Any]]:
    from palm.runtimes.mcp.config import PalmMcpConfig
    from palm.runtimes.mcp.in_process import create_in_process_backend
    from palm.runtimes.mcp.server import create_mcp_server

    config = PalmMcpConfig(
        base_url="http://127.0.0.1:8080",
        subject="dev",
        llms_txt_path=None,
        in_process=True,
        surface=surface,
    )
    backend = create_in_process_backend(config)
    mcp = create_mcp_server(config, client=backend)
    tools = await mcp.list_tools()
    rows: list[dict[str, Any]] = []
    for tool in tools:
        data = tool.model_dump() if hasattr(tool, "model_dump") else dict(tool)
        name = str(data.get("name") or "")
        desc = str(data.get("description") or "")
        params = data.get("parameters") or {}
        params_s = _jdump(params)
        desc_t = _est_tokens(desc)
        schema_t = _est_tokens(params_s)
        rows.append(
            {
                "name": name,
                "desc_chars": len(desc),
                "schema_chars": len(params_s),
                "desc_tokens_est": desc_t,
                "schema_tokens_est": schema_t,
                "total_tokens_est": _est_tokens(name) + desc_t + schema_t,
            }
        )
    rows.sort(key=lambda r: r["total_tokens_est"], reverse=True)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--surface",
        default="full",
        help="MCP surface profile: full | assist | core | experimental (default full)",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON report")
    parser.add_argument(
        "--top",
        type=int,
        default=15,
        help="Show top N tools by size (text mode, default 15)",
    )
    args = parser.parse_args()
    surface = str(args.surface).strip().lower()

    try:
        rows = asyncio.run(_list_tool_rows(surface))
    except ImportError as exc:
        print(f"error: {exc}", file=sys.stderr)
        print('Install MCP extra: pip install "palmengine[mcp]"', file=sys.stderr)
        return 1

    total = sum(r["total_tokens_est"] for r in rows)
    report = {
        "surface": surface,
        "tool_count": len(rows),
        "total_tokens_est": total,
        "desc_tokens_est": sum(r["desc_tokens_est"] for r in rows),
        "schema_tokens_est": sum(r["schema_tokens_est"] for r in rows),
        "tools": rows,
    }

    if args.json:
        print(json.dumps(report, indent=2))
        return 0

    print(f"surface={surface}")
    print(f"tool_count={len(rows)}")
    print(f"total_tokens_est≈{total}  (proxy: utf-8 chars/4)")
    print(
        f"  descriptions≈{report['desc_tokens_est']}  "
        f"schemas≈{report['schema_tokens_est']}"
    )
    print(f"--- top {min(args.top, len(rows))} ---")
    for row in rows[: args.top]:
        print(
            f"  {row['name']}: ≈{row['total_tokens_est']}t "
            f"(desc≈{row['desc_tokens_est']}, schema≈{row['schema_tokens_est']})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
