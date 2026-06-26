# Release checklist — 0.14.9

**Theme:** MCP Operator — coding-agent adapter for Palm wizards and flows

## Pre-release verification

- [ ] Version bumped: `pyproject.toml` and `src/palm/__init__.py` → **0.14.9**
- [ ] `CHANGELOG.md` — `[0.14.9]` section complete; `[Unreleased]` empty
- [ ] Docs updated: `README.md`, `ARCHITECTURE.md`, `STATUS.md`, `DEVELOPMENT.md`, `AGENTS.md`, `docs/MCP.md`, `docs/llms.txt`, `docs/index.html`
- [ ] `just docs-check` passes

## Quality gates

```bash
just docs-check       # version surfaces consistent
just check            # lint + mypy + tests + guard-core (~10s)
just full-check       # + demo-full + coverage
just demo-full        # ApplicationHost E2E script
```

Expected: **~791 tests** pass (`pytest --fast` skips slow integration).

MCP-specific:

```bash
uv sync --extra mcp
uv run pytest -q tests/test_mcp_tools.py tests/test_mcp_phase3.py \
  tests/test_mcp_phase4.py tests/test_mcp_phase5.py tests/test_mcp_http_surface.py \
  tests/test_mcp_registry.py tests/test_operator_waiting_jobs.py \
  tests/test_server_list_jobs_enrichment.py
```

Manual smoke:

```bash
palm version --full
palm doctor
just palm-server                    # terminal 1
just mcp-inspector                  # terminal 2 — optional
# In MCP Inspector: palm_doctor, palm://definitions/flows, palm_submit_wizard
```

## Build & publish

```bash
just release-prep
ls -lh dist/                   # palmengine-0.14.9-*
```

### TestPyPI (recommended first)

```bash
export TEST_PYPI_TOKEN=pypi-...
just publish-test
pip install -i https://test.pypi.org/simple/ 'palmengine[mcp]==0.14.9'
palm version
palm-mcp --help 2>/dev/null || uv run --extra mcp palm-mcp &
```

### Production PyPI

```bash
export PYPI_TOKEN=pypi-...
just publish                   # 5s abort window
```

Install extras:

```bash
pip install "palmengine[cli]"   # CLI + REPL
pip install "palmengine[mcp]"   # palm-mcp + FastMCP
```

## Git tag & GitHub

```bash
git add -A
git commit -m "Release 0.14.9 — MCP Operator"
git tag -a v0.14.9 -m "Palm Engine 0.14.9 — MCP Operator"
git push origin master --tags
```

Create GitHub release from tag `v0.14.9`:
- Title: **Palm Engine 0.14.9 — MCP Operator**
- Body: copy `CHANGELOG.md` `[0.14.9]` section
- Attach `dist/*` artifacts if not using CI publish

## Post-release

- [ ] Verify `pip install "palmengine[mcp]"` on clean venv
- [ ] Verify `palm-mcp` connects with running `palm server`
- [ ] Update website deployment if separate from repo
- [ ] Open `[Unreleased]` in `CHANGELOG.md` for next work

## Agent onboarding (communicate in release notes)

Coding agents should read [docs/MCP.md](docs/MCP.md) and load `palm://agent/guide` at session start.

**Operator loop:** definitions → submit → inspect → input → wait on children → resume

**Key conventions:** `instance_id` (not `job_id`); plain `input` strings; compact inspect by default.