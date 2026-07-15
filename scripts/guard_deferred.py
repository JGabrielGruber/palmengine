#!/usr/bin/env python3
"""Deferred-import guard (T3 / PD-012) — ratchets function-local palm imports toward zero.

Background: the audit's raw "595 deferred imports" grep conflates two things. Imports under
``if TYPE_CHECKING:`` are the *correct* way to reference cross-layer types and never run — they
are NOT debt and are excluded here. The debt is the runtime **function-local** ``import palm.`` /
``from palm.`` statements used to dodge circular imports, and especially the subset that point
**upward** into a higher layer (those are what actually force the cycles).

This guard is a ratchet: the two ceilings only ever move DOWN as 0.47 slices cut the seams
(see docs/VISION-0.47.md). It never rewrites code — it just fails ``just check`` / ``just ci``
if the counts regress or a new upward edge appears. Model: scripts/guard_core.py.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

# ── Ratchets — lower these as slices land; NEVER raise. Target: 0 upward. ─────────────
MAX_FUNCTION_LOCAL = 287  # total runtime function-local palm imports (0.47.1 baseline)
MAX_UPWARD = 35  # of those, imports into a strictly higher layer (cycle-forcing) — target 0

# Inward-pointing layer ranks (arrows point toward core). Higher rank imports lower rank.
LAYER_RANK = {
    "core": 0,
    "common": 1,
    "definitions": 2,
    "instances": 2,
    "states": 2,
    "storages": 2,
    "backends": 2,
    "patterns": 2,
    "providers": 2,
    "services": 2,
    "app": 3,
    "runtimes": 4,
}


def _layer(module: str) -> str | None:
    parts = module.split(".")
    return parts[1] if len(parts) >= 2 and parts[0] == "palm" else None


def _module_name(path: Path, root: Path) -> str:
    return "palm." + ".".join(path.relative_to(root).with_suffix("").parts)


def _palm_targets(node: ast.AST) -> list[str]:
    if isinstance(node, ast.ImportFrom):
        return [node.module] if node.module and node.module.split(".")[0] == "palm" else []
    if isinstance(node, ast.Import):
        return [a.name for a in node.names if a.name.split(".")[0] == "palm"]
    return []


def main() -> int:
    root = Path("src/palm")
    total = upward = 0
    direction = {"upward": 0, "sibling": 0, "downward": 0, "unranked": 0}
    upward_edges: list[str] = []
    per_file: dict[str, int] = {}

    for py in sorted(root.rglob("*.py")):
        try:
            tree = ast.parse(py.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        src_rank = LAYER_RANK.get(_layer(_module_name(py, root)), -1)

        tc_ids: set[int] = set()
        fn_ids: set[int] = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.If):
                test = n.test
                is_tc = (isinstance(test, ast.Name) and test.id == "TYPE_CHECKING") or (
                    isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING"
                )
                if is_tc:
                    for body_node in n.body:
                        for sub in ast.walk(body_node):
                            tc_ids.add(id(sub))
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for body_node in n.body:
                    for sub in ast.walk(body_node):
                        fn_ids.add(id(sub))

        for n in ast.walk(tree):
            targets = _palm_targets(n) if isinstance(n, (ast.Import, ast.ImportFrom)) else []
            if not targets or id(n) in tc_ids or id(n) not in fn_ids:
                continue
            for target in targets:
                total += 1
                per_file[str(py)] = per_file.get(str(py), 0) + 1
                tgt_rank = LAYER_RANK.get(_layer(target), -1)
                if src_rank < 0 or tgt_rank < 0:
                    direction["unranked"] += 1
                elif tgt_rank > src_rank:
                    direction["upward"] += 1
                    upward += 1
                    upward_edges.append(
                        f"{_layer(_module_name(py, root))} -> {_layer(target)}"
                        f"   {py.relative_to(root)}  ({target})"
                    )
                elif tgt_rank == src_rank:
                    direction["sibling"] += 1
                else:
                    direction["downward"] += 1

    print("deferred-import guard (T3 / PD-012)")
    print(f"  function-local palm imports : {total:4d}   (ceiling {MAX_FUNCTION_LOCAL})")
    print(f"  upward / cycle-forcing      : {upward:4d}   (ceiling {MAX_UPWARD})")
    print(f"  by direction                : {direction}")
    print("  top files:")
    for path_str, count in sorted(per_file.items(), key=lambda kv: kv[1], reverse=True)[:8]:
        print(f"    {count:3d}  {path_str}")

    failed = False
    if total > MAX_FUNCTION_LOCAL:
        print(f"[FAIL] {total} function-local palm imports > ceiling {MAX_FUNCTION_LOCAL} (ratchet only lowers)")
        failed = True
    if upward > MAX_UPWARD:
        print(f"[FAIL] {upward} upward palm imports > ceiling {MAX_UPWARD} — new cycle edge(s):")
        for edge in upward_edges:
            print(f"    {edge}")
        print("  Invert the dependency (contract in a lower layer) instead of a function-local import.")
        failed = True
    if failed:
        return 1

    print("[OK] deferred-import ceilings respected")
    return 0


if __name__ == "__main__":
    sys.exit(main())
