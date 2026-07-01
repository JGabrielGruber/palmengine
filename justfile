# =============================================================================
# Palm Orchestration Engine — Justfile
# PyPI distribution: palmengine · import package: palm · CLI: palm
# Run `just --list` to see all commands
# =============================================================================

set dotenv-load
set export

package := "palmengine"
dist_dir := "dist"
palm_data_dir := env_var_or_default('PALM_DATA_DIR', 'data')

# Default: show help
default:
    just --list --unsorted

# -----------------------------------------------------------------------------
# 1. Development Setup & Daily Flow
# -----------------------------------------------------------------------------
dev: setup hygiene
    @echo "✅ Ready to code! Use: just check, just test, just guard"

setup:
    uv sync --group dev --extra cli
    bash -c 'uv pip install --reinstall -e ".[cli]"'
    uv run pre-commit install
    @echo "✅ Environment synced ({{package}} editable + cli extra) + pre-commit installed"

hygiene:
    just format
    just lint-fix

# -----------------------------------------------------------------------------
# 2. Quality & Checking (the most used group)
# -----------------------------------------------------------------------------
check: lint typecheck test-quick guard-core guard-common

full-check: format lint typecheck test-full audit guard-core demo-full

lint:
    uv run ruff check src/palm/ tests/ examples/

lint-fix:
    uv run ruff check --fix src/palm/ tests/ examples/

format:
    uv run ruff format src/palm/ tests/ examples/

typecheck:
    uv run mypy src/palm/

test-quick:
    uv run pytest -q --tb=no

test-core:
    uv run pytest -q tests/core/ --tb=short

test-full:
    uv run pytest --cov=src/palm --cov-report=term-missing

test-watch:
    uv run ptw

# -----------------------------------------------------------------------------
# 3. Refactoring & Maintenance
# -----------------------------------------------------------------------------
refactor:
    @echo "🔍 Finding dead code..."
    uv run vulture src/palm/ --min-confidence 70
    @echo "🧹 Running autofixes..."
    just lint-fix
    uv run autoflake --remove-all-unused-imports --in-place --recursive src/palm/
    @echo "📊 Complexity report:"
    uv run radon cc src/palm/core/ --min C
    @echo "✅ Refactor pass done. Now run 'just full-check' and review."

# -----------------------------------------------------------------------------
# 4. Palm Architecture Guards (Critical for this project)
# -----------------------------------------------------------------------------
guard-core:
    @echo "🔒 Checking Core Purity Rules (0.6+ direction)..."
    uv run python scripts/guard_core.py

guard-common:
    @echo "🔒 Checking palm.common pattern boundary..."
    uv run pytest -q tests/test_common_boundary.py tests/test_provider_boundary.py tests/test_modular_apps.py --tb=short

sync-version:
    @echo "🔄 Syncing version to documentation surfaces..."
    uv run python scripts/sync_version.py

bump-version version:
    uv run python scripts/sync_version.py --set {{version}}

docs-check:
    @echo "📄 Checking documentation version consistency..."
    uv run python scripts/docs_check.py

guard-legacy:
    @echo "📌 Legacy package is reference-only — no new features here"

# -----------------------------------------------------------------------------
# 5. Audit & Security
# -----------------------------------------------------------------------------
audit: security complexity deps

security:
    uv run bandit -r src/palm/ -ll -ii
    uv run pip-audit

complexity:
    uv run radon cc src/palm/core/ -a
    uv run xenon --max-average A --max-modules B src/palm/

deps:
    uv pip compile pyproject.toml --output-file=requirements.txt --quiet
    @echo "✅ Dependency audit complete"

# -----------------------------------------------------------------------------
# 6. Palm CLI (requires palmengine[cli] or uv --extra cli)
# -----------------------------------------------------------------------------
palm *ARGS='--help':
    uv run --extra cli palm {{ARGS}}

palm-repl:
    uv run --extra cli palm repl

palm-doctor:
    uv run --extra cli palm doctor

palm-status:
    uv run --extra cli palm status

palm-status-full:
    uv run --extra cli palm status --full

palm-version:
    uv run --extra cli palm version --full

palm-demo-onboard:
    @echo "Starting onboarding wizard (interactive)…"
    uv run --extra cli palm wizard start onboard

palm-demo-approval:
    @echo "Starting approval workflow (interactive)…"
    uv run --extra cli palm wizard start approval

palm-server *ARGS='':
    uv run --extra cli palm host server {{ARGS}}

# -----------------------------------------------------------------------------
# 6a. Docker — Palm host server with filesystem storage
# -----------------------------------------------------------------------------
docker-build:
    docker compose build

docker-up *ARGS='':
    docker compose up -d {{ARGS}}

docker-down:
    docker compose down

docker-logs *ARGS='':
    docker compose logs -f {{ARGS}}

demo-full:
    uv run python examples/full_demo.py

# -----------------------------------------------------------------------------
# 6b. MCP — stdio adapter & Inspector
# https://modelcontextprotocol.io/docs/tools/inspector#inspecting-locally-developed-servers
# -----------------------------------------------------------------------------
mcp-sync:
    uv sync --group dev --extra mcp
    bash -c 'uv pip install --reinstall -e ".[mcp]"'
    @echo "✅ MCP extra synced (palm-mcp + fastmcp)"

mcp-inspector: mcp-sync
    @echo "🔍 MCP Inspector → palm-mcp (stdio)"
    @echo "   Docs: https://modelcontextprotocol.io/docs/tools/inspector"
    @echo "   Start Palm REST if needed: just palm-server"
    @echo "   PALM_BASE_URL=${PALM_BASE_URL:-http://127.0.0.1:8080}"
    npx -y @modelcontextprotocol/inspector uv --directory {{justfile_directory()}} run --extra mcp palm-mcp

# -----------------------------------------------------------------------------
# 7. Packaging & Release (PyPI name: palmengine)
# -----------------------------------------------------------------------------
clean-dist:
    rm -rf {{dist_dir}} build *.egg-info src/*.egg-info
    @echo "🧼 Cleaned build artifacts"

build: clean-dist
    uv build
    @ls -lh {{dist_dir}}/
    @echo "✅ Built {{package}} wheel + sdist in {{dist_dir}}/"

install-local:
    bash -c 'uv pip install --reinstall -e ".[cli,dev]"'
    @echo "✅ Editable install: {{package}} (import: palm, CLI: palm)"

publish-test: build
    @echo "📤 Publishing {{package}} to TestPyPI (test.pypi.org)..."
    @test -n "${TEST_PYPI_TOKEN:-}" || (echo "Set TEST_PYPI_TOKEN (PyPI API token for TestPyPI)" && exit 1)
    uv publish --publish-url https://test.pypi.org/legacy/ --token "${TEST_PYPI_TOKEN}"
    @echo '✅ Published to TestPyPI. Try: pip install -i https://test.pypi.org/simple/ palmengine[cli]'

publish: build
    @echo "⚠️  WARNING: Publishing {{package}} to PRODUCTION PyPI!"
    @echo "    Verify version in pyproject.toml and CHANGELOG.md first."
    @echo "    Press Ctrl+C within 5 seconds to abort..."
    @sleep 5
    @test -n "${PYPI_TOKEN:-}" || (echo "Set PYPI_TOKEN (PyPI API token)" && exit 1)
    uv publish --token "${PYPI_TOKEN}"
    @echo '✅ Published to PyPI. Users can: pip install palmengine[cli]'

docs-build:
    cd docs && npx @tailwindcss/cli -i styles/input.css -o styles/output.css
    @echo "✅ docs/styles/output.css rebuilt"

release-prep:
    @echo "📋 Release prep for {{package}}"
    @echo "   Version: $(uv run python -c 'import palm; print(palm.__version__)')"
    just sync-version
    just docs-check
    just full-check
    just build
    @echo "🎉 Release prep complete — review dist/, CHANGELOG.md, RELEASE-0.15.4.md"

# -----------------------------------------------------------------------------
# 8. Convenience & CI-friendly
# -----------------------------------------------------------------------------
prepr: full-check
    @echo "🎉 Palm quality gates passed — ready for release review!"

clean: clean-dist
    @mkdir -p {{palm_data_dir}}
    @test -d {{palm_data_dir}} && find {{palm_data_dir}} -mindepth 1 ! -name .gitkeep -exec rm -rf {} +
    @touch {{palm_data_dir}}/.gitkeep
    find src -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    rm -rf .pytest_cache .ruff_cache .mypy_cache .cache *.db
    @echo "🧼 Cleaned temporary files"

# -----------------------------------------------------------------------------
# Help & Discovery
# -----------------------------------------------------------------------------
help:
    @echo "🌴 Palm Tooling Commands:"
    @echo "   just dev              → Full setup + hygiene"
    @echo "   just check            → Fast quality check + guard-core + guard-common"
    @echo "   just test-core        → Pure palm.core contract tests"
    @echo "   just full-check       → Everything + demo-full"
    @echo "   just prepr            → Pre-release gate"
    @echo "   just build            → Clean + wheel + sdist"
    @echo "   just install-local    → Editable palmengine install"
    @echo "   just publish-test     → Build + TestPyPI"
    @echo "   just publish          → Build + PyPI (5s warning)"
    @echo "   just guard-common     → palm.common pattern boundary tests"
    @echo "   just docs-check       → Version + documentation surface consistency"
    @echo "   just docs-build       → Rebuild docs site Tailwind CSS"
    @echo "   just release-prep     → docs-check + full-check + build"
    @echo "   just demo-full        → examples/full_demo.py"
    @echo "   just mcp-inspector    → MCP Inspector UI for palm-mcp"
    @echo "   just palm-server      → Palm HTTP API (REST backend for MCP)"
    @echo "   just docker-up        → Palm host server in Docker (./data + ./logs)"
    @echo "   just clean            → Remove data/ + tool caches"
    @echo "   just palm --help      → CLI command list"
    @echo "Run 'just --list' for full list"