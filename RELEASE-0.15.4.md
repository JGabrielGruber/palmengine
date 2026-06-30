# Release checklist — 0.15.4

**Theme:** CQRS Schemas + Service Layer — unified user-facing API, in-process MCP, cleanup track

## Pre-release verification

- [x] Version bumped: `pyproject.toml` and `src/palm/__init__.py` → **0.15.4**
- [x] `CHANGELOG.md` — `[0.15.4]` section complete; `[Unreleased]` empty
- [x] Docs updated: `README.md`, `ARCHITECTURE.md`, `STATUS.md`, `DEVELOPMENT.md`, `docs/MCP.md`, `docs/llms.txt`, `docs/index.html`
- [ ] `just docs-check` passes (includes bundled `src/palm/runtimes/mcp/data/llms.txt`)

## Quality gates

```bash
just docs-check       # version surfaces consistent
uv run ruff check src/palm/ tests/
uv run pytest tests/test_cqrs_schemas.py tests/test_services_*.py \
  tests/test_mcp_in_process.py tests/test_rest_schema_bridge.py \
  tests/test_server_wizards.py tests/test_mcp_tools.py -v
just guard-common
```

Optional full gate (mypy may report pre-existing issues):

```bash
just check
just full-check
just demo-full
```

## 0.15-specific smoke

```bash
# In-process MCP (no REST server)
PALM_MCP_IN_PROCESS=1 uv run --extra mcp palm-mcp

# Service layer (Python)
uv run python -c "
from palm.app.session import create_cli_host
host = create_cli_host()
host.start()
print('services:', host.internal, host.execution, host.definition)
host.stop()
"

palm version --full
palm doctor
```

## Build & publish

```bash
just release-prep
ls -lh dist/                   # palmengine-0.15.4-*
```

### TestPyPI (recommended first)

```bash
export TEST_PYPI_TOKEN=pypi-...
just publish-test
pip install -i https://test.pypi.org/simple/ 'palmengine[mcp]==0.15.4'
palm version
```

### Production PyPI

```bash
export PYPI_TOKEN=pypi-...
just publish                   # 5s abort window
```

Install extras:

```bash
pip install "palmengine[cli]"   # CLI + REPL
pip install "palmengine[mcp]"   # palm-mcp + FastMCP (in-process default)
```

## Git tag & GitHub

```bash
git add -A
git commit -m "Release 0.15.4 — CQRS schemas + service layer"
git tag -a v0.15.4 -m "Palm Engine 0.15.4 — Service layer + in-process MCP"
git push origin master --tags
```

Create GitHub release from tag `v0.15.4`:
- Title: **Palm Engine 0.15.4 — CQRS Schemas + Service Layer**
- Body: copy `CHANGELOG.md` `[0.15.4]` section

## Post-release

- [ ] Update `STATUS.md` priorities → 0.16+ features
- [ ] Verify `pip install palmengine==0.15.4` on clean venv