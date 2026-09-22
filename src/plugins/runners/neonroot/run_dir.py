"""Palm-owned hermetic run directories for NeonRoot bind/copy (0.54.8).

Stages a small host tree NeonRoot can ``--seed`` (prefer ``seed_mode=bind``
for live write-back into ``output/``). Does **not** store workspace trees in
the engine — only paths returned for job params / state.

Layout::

    {data_dir}/palm/hermetic/runs/{run_id}/
      payload/
      input/
      output/
      meta.json
"""

from __future__ import annotations

import json
import shutil
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass
class HermeticRunDir:
    """Paths for one hermetic job staging area."""

    run_id: str
    root: Path
    payload: Path
    input: Path
    output: Path
    meta_path: Path

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "root": str(self.root),
            "payload": str(self.payload),
            "input": str(self.input),
            "output": str(self.output),
            "meta_path": str(self.meta_path),
        }

    def neonroot_spawn_params(
        self,
        *,
        image: str,
        command: list[str],
        seed_mode: str = "bind",
        vault: str | None = None,
        sandbox: bool = True,
        **extra: Any,
    ) -> dict[str, Any]:
        """Build neonroot ``spawn`` params seeding this run dir."""
        params: dict[str, Any] = {
            "image": image,
            "command": list(command),
            "seed": str(self.root.resolve()),
            "seed_mode": seed_mode,
            "sandbox": sandbox,
        }
        if vault:
            params["vault"] = vault
        params.update(extra)
        return params


def default_runs_root(data_dir: str | Path | None = None) -> Path:
    """``{data_dir}/palm/hermetic/runs`` or ``./data/palm/hermetic/runs``."""
    base = Path(data_dir) if data_dir is not None else Path("data")
    return (base / "palm" / "hermetic" / "runs").resolve()


def create_run_dir(
    *,
    data_dir: str | Path | None = None,
    run_id: str | None = None,
    meta: dict[str, Any] | None = None,
) -> HermeticRunDir:
    """Create a fresh run directory with payload/input/output subdirs."""
    rid = (run_id or uuid.uuid4().hex).strip()
    if not rid or "/" in rid or ".." in rid:
        raise ValueError(f"invalid run_id {run_id!r}")
    root = default_runs_root(data_dir) / rid
    payload = root / "payload"
    input_dir = root / "input"
    output_dir = root / "output"
    for d in (payload, input_dir, output_dir):
        d.mkdir(parents=True, exist_ok=True)
    meta_path = root / "meta.json"
    record = {
        "run_id": rid,
        "created_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **dict(meta or {}),
    }
    meta_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return HermeticRunDir(
        run_id=rid,
        root=root,
        payload=payload,
        input=input_dir,
        output=output_dir,
        meta_path=meta_path,
    )


def write_payload_file(run: HermeticRunDir, relative: str, content: str | bytes) -> Path:
    """Write a file under ``payload/`` (no path traversal)."""
    rel = relative.strip().replace("\\", "/")
    if not rel or rel.startswith("/") or ".." in rel.split("/"):
        raise ValueError(f"invalid payload path {relative!r}")
    path = run.payload / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8")
    return path


def remove_run_dir(run: HermeticRunDir | Path, *, missing_ok: bool = True) -> None:
    """GC a run directory after success (or TTL policy elsewhere)."""
    root = run.root if isinstance(run, HermeticRunDir) else Path(run)
    if root.exists():
        shutil.rmtree(root)
    elif not missing_ok:
        raise FileNotFoundError(root)


__all__ = [
    "HermeticRunDir",
    "create_run_dir",
    "default_runs_root",
    "remove_run_dir",
    "write_payload_file",
]
