"""WorkloadSpec → NeonRoot SpawnRequest (normative adapter).

Seed vocabulary (portable Spec ``seed`` dict)::

    None                         → hermetic: git_archive · best_effort: none
    {type: none}                 → no seed
    {type: git_archive}          → git archive HEAD
    {type: path, path: "…"}      → host dir (seed_mode copy by default)
    {type: bind, path: "…"}      → host dir bind mount
    {type: path|bind, exclude: […], mode: copy|bind}

Extras (not core Spec fields) ride in ``resources`` / ``labels``::

    resources.vault / labels.vault
    resources.outputs / resources.output
    labels.name → neonroot workspace name
"""

from __future__ import annotations

from typing import Any

from palm.core.workload.spec import IsolationPolicy, WorkloadSpec
from plugins.runners.neonroot.spawn import SpawnRequest, _normalize_outputs

_DEFAULT_TIMEOUT = 3600.0


def spawn_request_from_spec(spec: WorkloadSpec) -> SpawnRequest:
    """Build a validated :class:`SpawnRequest` from a portable WorkloadSpec."""
    image = spec.image_or_ref
    if not image or not str(image).strip():
        raise ValueError("neonroot requires WorkloadSpec.image or image_ref")
    if not spec.command:
        raise ValueError("neonroot requires non-empty WorkloadSpec.command (argv)")

    seed, seed_mode, seed_exclude = _resolve_seed(spec)
    vault = _opt_str(spec.resources.get("vault")) or _opt_str(spec.labels.get("vault"))
    name = _opt_str(spec.labels.get("name")) or _opt_str(spec.labels.get("workload_name"))
    outputs = _normalize_outputs(
        spec.resources.get("outputs") or spec.resources.get("output")
    )
    timeout = float(spec.timeout_s) if spec.timeout_s is not None else _DEFAULT_TIMEOUT
    if timeout <= 0:
        raise ValueError("timeout_s must be positive")

    # hermetic ⇒ isolated (no network) by default; best_effort stays sandboxed
    isolated = spec.isolation is IsolationPolicy.HERMETIC
    sandbox = True
    if "sandbox" in spec.resources:
        sandbox = bool(spec.resources["sandbox"])
    if "isolated" in spec.resources:
        isolated = bool(spec.resources["isolated"])

    return SpawnRequest(
        image=str(image).strip(),
        command=tuple(str(c) for c in spec.command),
        vault=vault,
        name=name,
        seed=seed,
        sandbox=sandbox,
        isolated=isolated,
        keep=bool(spec.resources.get("keep", False)),
        timeout=timeout,
        cwd=_opt_str(spec.workdir) or _opt_str(spec.resources.get("repo_root")),
        seed_exclude=seed_exclude,
        outputs=outputs,
        seed_mode=seed_mode,
    )


def _resolve_seed(spec: WorkloadSpec) -> tuple[str, str, tuple[str, ...]]:
    """Return (seed, seed_mode, seed_exclude)."""
    raw = spec.seed
    if raw is None:
        if spec.isolation is IsolationPolicy.HERMETIC:
            return "git-archive", "copy", ()
        return "none", "copy", ()

    if isinstance(raw, str):
        # Legacy: bare string path or git-archive / none
        text = raw.strip()
        if text in ("", "none", "false", "no"):
            return "none", "copy", ()
        if text in ("git-archive", "git_archive"):
            return "git-archive", "copy", ()
        return text, "copy", ()

    if not isinstance(raw, dict):
        raise ValueError("WorkloadSpec.seed must be a dict, string, or null")

    stype = str(raw.get("type") or raw.get("mode") or "").strip().lower()
    exclude_raw = raw.get("exclude") or raw.get("seed_exclude") or ()
    if isinstance(exclude_raw, str):
        exclude = (exclude_raw,) if exclude_raw.strip() else ()
    elif isinstance(exclude_raw, list | tuple):
        exclude = tuple(str(x) for x in exclude_raw if str(x).strip())
    else:
        exclude = ()

    mode = str(raw.get("seed_mode") or raw.get("mode") or "copy").strip().lower()
    if mode not in ("copy", "bind") and stype != "bind":
        mode = "copy"
    if stype == "bind":
        mode = "bind"

    if stype in ("none", "omit", "false", "no"):
        return "none", "copy", ()
    if stype in ("git_archive", "git-archive", ""):
        if stype == "" and (raw.get("path") or raw.get("uri")):
            # {path: "..."} without type → path seed
            path = str(raw.get("path") or raw.get("uri") or "").strip()
            if not path:
                raise ValueError("seed path/uri is empty")
            if mode == "bind" and exclude:
                raise ValueError("seed_mode=bind does not support exclude")
            return path, mode, exclude if mode == "copy" else ()
        return "git-archive", "copy", exclude
    if stype in ("path", "uri", "bind", "dir"):
        path = str(raw.get("path") or raw.get("uri") or "").strip()
        if not path:
            raise ValueError(f"seed type={stype!r} requires path or uri")
        if mode == "bind" and exclude:
            raise ValueError("seed_mode=bind does not support exclude")
        if stype == "bind":
            mode = "bind"
        return path, mode, exclude if mode == "copy" else ()

    raise ValueError(
        f"unknown WorkloadSpec.seed type {stype!r}; "
        "use none|git_archive|path|bind"
    )


def _opt_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


__all__ = ["spawn_request_from_spec"]
