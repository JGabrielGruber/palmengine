"""NeonRoot ``spawn`` action — hermetic command run (0.53.2+).

Maps to::

    neonroot spawn [name] --image <img> [--vault …] [--sandbox] [--isolated]
        [--seed <dir>] [--seed-exclude …] [--output host:container …]
        -- <command…>

``seed`` policy (ADR-022):

- ``git-archive`` (default for hermetic claims) — ``git archive HEAD`` into a
  temp directory, seed that path, delete after spawn.
- absolute/relative path — seed that host directory; prefer narrow paths
  (e.g. ``docs/``) or repo root **with** ``seed_exclude`` / ``.neonrootignore``.
- omit / empty with seed ``none`` — no ``--seed`` flag.

``outputs`` (NeonRoot  — export after **successful** exit only)::

    [{"host": "docs/styles/output.css", "container": "styles/output.css"}]
    # or strings "host:container"
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from plugins.runners.neonroot.cli import find_neonroot_binary, probe_neonroot

# Captured stream tails — enough for doctor / Assist, not full log dumps.
_DEFAULT_TAIL = 8000
_DEFAULT_TIMEOUT = 3600.0


@dataclass(frozen=True)
class SpawnRequest:
    """Validated spawn parameters."""

    image: str
    command: tuple[str, ...]
    vault: str | None = None
    name: str | None = None
    seed: str = "git-archive"
    sandbox: bool = True
    isolated: bool = False
    keep: bool = False
    timeout: float = _DEFAULT_TIMEOUT
    cwd: str | None = None  # git-archive root; default: process cwd / repo
    seed_exclude: tuple[str, ...] = ()
    outputs: tuple[str, ...] = ()  # each "host:container"
    seed_mode: str = "copy"  # copy (hermetic, default) | bind (live host mount; NeonRoot 0.2+)


def _as_str_list(value: Any, *, field_name: str, allow_empty: bool = False) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        parts = value.strip().split()
        if not parts and not allow_empty:
            raise ValueError(f"{field_name} must be a non-empty command list or string")
        return parts
    if isinstance(value, list | tuple):
        out = [str(x) for x in value]
        if not out and not allow_empty:
            raise ValueError(f"{field_name} must be a non-empty list")
        return out
    raise ValueError(f"{field_name} must be a list of strings (got {type(value).__name__})")


def _normalize_outputs(value: Any) -> tuple[str, ...]:
    """Accept list of 'host:container' strings or {host, container} maps."""
    if value is None:
        return ()
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list | tuple):
        raise ValueError("outputs must be a list of 'host:container' or {host, container}")
    out: list[str] = []
    for item in value:
        if isinstance(item, str):
            if ":" not in item:
                raise ValueError(
                    f"output map must be host:container (got {item!r})"
                )
            host, _, container = item.partition(":")
            if not host.strip() or not container.strip():
                raise ValueError(f"invalid output map {item!r}")
            if container.strip().startswith("/") or ".." in Path(container).parts:
                raise ValueError(
                    f"container path must be relative and not escape (got {container!r})"
                )
            out.append(f"{host.strip()}:{container.strip()}")
        elif isinstance(item, dict):
            host = str(item.get("host") or "").strip()
            container = str(item.get("container") or item.get("guest") or "").strip()
            if not host or not container:
                raise ValueError("output dict needs host and container keys")
            if container.startswith("/") or ".." in Path(container).parts:
                raise ValueError(
                    f"container path must be relative and not escape (got {container!r})"
                )
            out.append(f"{host}:{container}")
        else:
            raise ValueError(f"unsupported output entry type {type(item).__name__}")
    return tuple(out)


def parse_spawn_params(params: dict[str, Any]) -> SpawnRequest:
    """Build a :class:`SpawnRequest` from provider invoke params."""
    image = params.get("image")
    if not image or not str(image).strip():
        raise ValueError("spawn requires params.image (NeonRoot image name)")

    command = _as_str_list(params.get("command"), field_name="command")
    if not command:
        raise ValueError("spawn requires params.command (non-empty argv list)")
    vault = params.get("vault")
    name = params.get("name")
    seed = params.get("seed", "git-archive")
    if seed is None:
        seed = "git-archive"
    seed = str(seed)

    sandbox = bool(params.get("sandbox", True))
    isolated = bool(params.get("isolated", False))
    keep = bool(params.get("keep", False))
    timeout = float(params.get("timeout", _DEFAULT_TIMEOUT))
    if timeout <= 0:
        raise ValueError("timeout must be positive")

    seed_exclude = tuple(
        _as_str_list(
            params.get("seed_exclude") or params.get("seed_excludes"),
            field_name="seed_exclude",
            allow_empty=True,
        )
    )
    outputs = _normalize_outputs(params.get("outputs") or params.get("output"))

    seed_mode = str(params.get("seed_mode") or "copy").strip().lower()
    if seed_mode not in ("copy", "bind"):
        raise ValueError("seed_mode must be 'copy' or 'bind'")
    if seed_mode == "bind":
        if seed in ("", "none", "false", "no", "git-archive"):
            raise ValueError(
                "seed_mode=bind requires params.seed as a host directory path "
                "(not git-archive/none)"
            )
        if seed_exclude:
            raise ValueError(
                "seed_mode=bind does not support seed_exclude "
                "(NeonRoot rejects exclude with bind)"
            )

    cwd = params.get("cwd") or params.get("repo_root")
    return SpawnRequest(
        image=str(image).strip(),
        command=tuple(command),
        vault=str(vault).strip() if vault else None,
        name=str(name).strip() if name else None,
        seed=seed,
        sandbox=sandbox,
        isolated=isolated,
        keep=keep,
        timeout=timeout,
        cwd=str(cwd) if cwd else None,
        seed_exclude=seed_exclude,
        outputs=outputs,
        seed_mode=seed_mode,
    )


def _tail(text: str, limit: int = _DEFAULT_TAIL) -> str:
    if len(text) <= limit:
        return text
    return text[-limit:]


def _prepare_seed(
    seed: str,
    *,
    repo_root: Path,
) -> tuple[str | None, Path | None]:
    """Return (seed_path_for_cli, temp_dir_to_cleanup)."""
    if seed in ("", "none", "false", "no"):
        return None, None
    if seed == "git-archive":
        tmp = Path(tempfile.mkdtemp(prefix="palm-neonroot-seed-"))
        try:
            proc = subprocess.run(
                ["git", "archive", "HEAD"],
                cwd=repo_root,
                capture_output=True,
                check=False,
            )
            if proc.returncode != 0:
                err = (proc.stderr or proc.stdout or b"").decode("utf-8", errors="replace")
                shutil.rmtree(tmp, ignore_errors=True)
                raise RuntimeError(f"git archive HEAD failed: {err.strip() or proc.returncode}")
            subprocess.run(
                ["tar", "-x", "-C", str(tmp)],
                input=proc.stdout,
                check=True,
            )
        except Exception:
            shutil.rmtree(tmp, ignore_errors=True)
            raise
        return str(tmp), tmp

    path = Path(seed).expanduser()
    if not path.is_absolute():
        path = (repo_root / path).resolve()
    else:
        path = path.resolve()
    if not path.is_dir():
        raise ValueError(f"seed path is not a directory: {path}")
    return str(path), None


def build_spawn_argv(
    neonroot_bin: str,
    req: SpawnRequest,
    *,
    seed_path: str | None,
    repo_root: Path | None = None,
) -> list[str]:
    """Construct the ``neonroot spawn …`` argv (no shell)."""
    argv: list[str] = [neonroot_bin, "spawn"]
    if req.name:
        argv.append(req.name)
    argv.extend(["--image", req.image])
    if req.vault:
        argv.extend(["--vault", req.vault])
    if req.isolated:
        argv.append("--isolated")
    elif req.sandbox:
        argv.append("--sandbox")
    if req.keep:
        argv.append("--keep")
    if seed_path:
        argv.extend(["--seed", seed_path])
        if req.seed_mode and req.seed_mode != "copy":
            argv.extend(["--seed-mode", req.seed_mode])
    for excl in req.seed_exclude:
        argv.extend(["--seed-exclude", excl])
    root = repo_root or Path.cwd()
    for mapping in req.outputs:
        host, _, container = mapping.partition(":")
        host_path = Path(host)
        if not host_path.is_absolute():
            host_path = (root / host_path).resolve()
        argv.extend(["--output", f"{host_path}:{container}"])
    argv.append("--")
    argv.extend(req.command)
    return argv


def run_spawn_request(
    req: SpawnRequest,
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Execute a validated :class:`SpawnRequest`; return serializable result dict."""
    probe = probe_neonroot()
    if not probe.available or not probe.path:
        raise RuntimeError(probe.error or "neonroot not available")

    root = Path(req.cwd) if req.cwd else (repo_root or Path.cwd())
    root = root.resolve()

    seed_path, cleanup = _prepare_seed(req.seed, repo_root=root)
    argv = build_spawn_argv(probe.path, req, seed_path=seed_path, repo_root=root)
    started = time.monotonic()
    try:
        proc = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=req.timeout,
            check=False,
            cwd=str(root),
        )
        duration = time.monotonic() - started
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
        return {
            "exit_code": proc.returncode,
            "duration_s": round(duration, 3),
            "argv": argv,
            "image": req.image,
            "vault": req.vault,
            "seed": req.seed,
            "seed_path": seed_path,
            "seed_exclude": list(req.seed_exclude),
            "seed_mode": req.seed_mode,
            "outputs": list(req.outputs),
            "sandbox": req.sandbox,
            "isolated": req.isolated,
            "command": list(req.command),
            "stdout_tail": _tail(stdout),
            "stderr_tail": _tail(stderr),
            "neonroot": probe.as_dict(),
        }
    except subprocess.TimeoutExpired as exc:
        duration = time.monotonic() - started
        stdout = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
        stderr = (exc.stderr or "") if isinstance(exc.stderr, str) else ""
        return {
            "exit_code": None,
            "timed_out": True,
            "duration_s": round(duration, 3),
            "argv": argv,
            "image": req.image,
            "vault": req.vault,
            "seed": req.seed,
            "seed_path": seed_path,
            "seed_exclude": list(req.seed_exclude),
            "seed_mode": req.seed_mode,
            "outputs": list(req.outputs),
            "command": list(req.command),
            "stdout_tail": _tail(stdout),
            "stderr_tail": _tail(stderr or f"timeout after {req.timeout}s"),
            "neonroot": probe.as_dict(),
            "error": f"spawn timed out after {req.timeout}s",
            "error_class": "timeout",
        }
    finally:
        if cleanup is not None:
            shutil.rmtree(cleanup, ignore_errors=True)


def run_spawn(
    params: dict[str, Any],
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Execute spawn from a loose param dict (tests / tooling). Prefer Spec path."""
    return run_spawn_request(parse_spawn_params(params), repo_root=repo_root)


def resolve_repo_root() -> Path:
    """Best-effort package / checkout root (for git-archive)."""
    here = Path(__file__).resolve()
    candidate = here.parents[4]
    if (candidate / "pyproject.toml").is_file():
        return candidate
    binary = find_neonroot_binary()
    _ = binary
    return Path.cwd()


__all__ = [
    "SpawnRequest",
    "build_spawn_argv",
    "parse_spawn_params",
    "resolve_repo_root",
    "run_spawn",
    "run_spawn_request",
]
