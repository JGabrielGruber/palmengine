# Release checklist — 0.16.5

**Theme:** Services Are the API — `palm/services/`, `/v1/api/…` REST, per-domain MCP, breaking legacy transport

## Pre-release verification

- [x] Version bumped: `pyproject.toml` and `src/palm/__init__.py` → **0.16.5**
- [x] `CHANGELOG.md` — `[0.16.5]` section complete; `[Unreleased]` empty
- [x] Docs updated: `README.md`, `ARCHITECTURE.md`, `STATUS.md`, `DEVELOPMENT.md`, `docs/MCP.md`, `docs/llms.txt`, `docs/index.html`, `AGENTS.md`, `MIGRATION-0.16.md`, `docs/VISION-0.16.md`
- [ ] `just docs-check` passes (includes bundled `src/palm/runtimes/mcp/data/llms.txt`)

## Quality gates

```bash
just docs-check
just guard-common
uv run pytest tests/test_service_registries.py tests/test_definitions_catalog.py \
  tests/test_mcp_in_process.py tests/test_mcp_domain_tools.py \
  tests/test_server_wizards.py tests/test_rest_definitions_crud.py \
  tests/test_rest_resources_invoke.py -v
```

## 0.16-specific smoke

```bash
# In-process MCP (no REST server)
PALM_MCP_IN_PROCESS=1 uv run --extra mcp palm-mcp

# Service layer (Python)
uv run python -c "
from palm.app.session import create_cli_host
host = create_cli_host()
host.start()
print('services:', host.system, host.execution, host.definitions)
host.stop()
"

palm version --full
palm doctor
```

## Build & publish

```bash
just release-prep
ls -lh dist/                   # palmengine-0.16.5-*
```

### TestPyPI (recommended first)

```bash
export TEST_PYPI_TOKEN=pypi-...
just publish-test
pip install -i https://test.pypi.org/simple/ 'palmengine[mcp]==0.16.5'
palm version
```

### Production PyPI

```bash
export PYPI_TOKEN=pypi-...
just publish                   # 5s abort window
```

## Git tag & GitHub

```bash
git add -A
git commit -m "feat(0.16.5): docs, version bump, and legacy handler cleanup"
git tag -a v0.16.5 -m "Palm Engine 0.16.5 — Services are the API"
git push origin master --tags
```

Create GitHub release from tag `v0.16.5`:
- Title: **Palm Engine 0.16.5 — Services Are the API**
- Body: copy `CHANGELOG.md` `[0.16.5]` section

## Post-release

- [ ] Verify `pip install palmengine==0.16.5` on clean venv
- [ ] Announce breaking REST/MCP changes — point integrators to `MIGRATION-0.16.md`