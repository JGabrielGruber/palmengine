"""0.71.18 — surface / MCP payload trees stay out of the base wheel.

Pip extras cannot strip wheel files. Hatch wheel ``artifacts`` must not force
SSR/Portal/Analytics static or ``mcp/data`` into the wheel. Source / sdist keep
them for editable and checkout use.
"""

from __future__ import annotations

import subprocess
import tempfile
import zipfile
from pathlib import Path

import tomllib

REPO_ROOT = Path(__file__).resolve().parents[1]

# Paths as they appear inside the built wheel (no ``src/`` prefix).
WHEEL_FORBIDDEN_PREFIXES = (
    "palm/runtimes/server/surfaces/ssr/studio/static/",
    "palm/runtimes/server/surfaces/websocket/static/",
    "palm/runtimes/server/surfaces/rest/analytics/static/",
    "palm/runtimes/mcp/data/",
)

# Repo-relative trees that must be excluded from the wheel target.
HATCH_FORBIDDEN_PREFIXES = (
    "src/palm/runtimes/server/surfaces/ssr/studio/static/",
    "src/palm/runtimes/server/surfaces/websocket/static/",
    "src/palm/runtimes/server/surfaces/rest/analytics/static/",
    "src/palm/runtimes/mcp/data/",
)


def _wheel_target() -> dict:
    data = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return data["tool"]["hatch"]["build"]["targets"]["wheel"]


def _pattern_covers(pattern: str, prefix: str) -> bool:
    """True when a hatch glob covers ``prefix`` (directory tree)."""
    p = pattern.replace("\\", "/").rstrip("/")
    target = prefix.replace("\\", "/").rstrip("/")
    if p.endswith("/**"):
        p = p[: -len("/**")]
    elif p.endswith("/**/*"):
        p = p[: -len("/**/*")]
    return p == target or target.startswith(p + "/") or p.startswith(target)


def test_hatch_wheel_config_excludes_surface_assets() -> None:
    """Config pin: exclude those trees; artifacts must not force them back in."""
    wheel = _wheel_target()
    exclude = [str(p) for p in wheel.get("exclude", [])]
    artifacts = [str(p) for p in wheel.get("artifacts", [])]

    for prefix in HATCH_FORBIDDEN_PREFIXES:
        assert any(
            _pattern_covers(pattern, prefix) for pattern in exclude
        ), f"wheel exclude must cover {prefix!r}; got {exclude!r}"

    for pattern in artifacts:
        assert not any(
            _pattern_covers(pattern, prefix) for prefix in HATCH_FORBIDDEN_PREFIXES
        ), f"wheel artifacts must not force {pattern!r}"


def test_built_wheel_omits_surface_assets() -> None:
    """Real hatchling/uv wheel must not contain static or mcp/data trees."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        result = subprocess.run(
            ["uv", "build", "--wheel", "--out-dir", str(out)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr or result.stdout
        wheels = sorted(out.glob("palmengine-*.whl"))
        assert len(wheels) == 1, f"expected one wheel, got {wheels!r}"

        with zipfile.ZipFile(wheels[0]) as zf:
            names = [n.replace("\\", "/") for n in zf.namelist()]

        for prefix in WHEEL_FORBIDDEN_PREFIXES:
            hits = [n for n in names if n == prefix.rstrip("/") or n.startswith(prefix)]
            assert not hits, f"wheel must omit {prefix!r}; found {hits[:12]!r}"
