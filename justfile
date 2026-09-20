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
ci_flags := "--extra cli --extra mcp --extra dotenv --group dev"

# Default: show help
default:
    just --list --unsorted

# -----------------------------------------------------------------------------
# 1. Development Setup & Daily Flow
# -----------------------------------------------------------------------------
dev: setup hygiene
    @echo "✅ Ready to code! Use: just check, just test, just guard"

setup:
    uv sync --group dev --extra cli --extra dotenv
    bash -c 'uv pip install --reinstall -e ".[cli,dotenv]"'
    uv run pre-commit install
    @echo "✅ Environment synced ({{package}} editable + cli/dotenv extras) + pre-commit installed"

hygiene:
    just format
    just lint-fix

# -----------------------------------------------------------------------------
# 2. Quality & Checking (the most used group)
# -----------------------------------------------------------------------------
check: lint typecheck test-quick guard-core guard-common guard-system guard-assembly guard-deferred

full-check: format lint typecheck test-full audit guard-core guard-assembly demo-full

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

guard-system:
    @echo "🔒 Checking palm.system import rules (0.57+)..."
    uv run python scripts/guard_system.py
    uv run pytest -q tests/test_system_boundary.py --tb=short

# Assembly coherence (0.63.4) — fail-closed admission; red maps dual mode.
guard-assembly:
    uv run python scripts/guard_assembly.py

# Deferred-import ratchet (T3 / PD-012) — function-local palm imports may only decrease.
guard-deferred:
    @echo "🔒 Checking deferred-import ratchet (T3 / PD-012)..."
    uv run python scripts/guard_deferred.py

sync-version:
    @echo "🔄 Syncing version to documentation surfaces..."
    uv run python scripts/sync_version.py

# MCP catalog size inventory (0.31.1) — progressive disclosure / token proxy
mcp-inventory surface='full':
    @echo "📊 MCP tool catalog inventory (surface={{surface}})..."
    uv run --extra mcp python scripts/mcp_catalog_inventory.py --surface {{surface}}

bump-version version:
    # Stamps version surfaces *and* copies docs → MCP/Grok mirrors (PD-031 / 0.52.1)
    uv run python scripts/sync_version.py --set {{version}}

docs-sync-mirrors:
    @echo "📄 Syncing docs/ → MCP data + .grok skill mirrors..."
    uv run python scripts/sync_version.py

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
    uv run --extra cli palm flow start onboard

palm-demo-approval:
    @echo "Starting approval workflow (interactive)…"
    uv run --extra cli palm flow start approval

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

# ---- Website (palmengine.org) — SOURCE website/ · BUILD website/dist ----

# Tailwind for website/styles (host Node or npx). Prefer website-css-sandbox on thin desks.
website-css:
    bash scripts/website_css.sh

# Assemble static canopy → website/dist (Cloudflare assets.directory).
website-build:
    @echo "🌴 Building website → website/dist/…"
    uv run python scripts/website_build.py
    @echo "✅ Cloudflare: assets directory = website/dist  (project root = repo)"

# CSS then dist (what you usually run before commit/deploy).
website-build-all: website-css website-build

# Previeww
website-preview:
    python -m http.server 8765 --directory website/dist

# Build all + preview
website-dev: website-build-all website-preview

# ---- Living Library (docs only; not palmengine.org) ----

# Living Library → docs/_build/ (wiki + reference inventory). No website.
docs-build:
    @echo "📚 Building Living Library → docs/_build/…"
    uv run python scripts/docs_build.py
    @echo "✅ docs/_build ready (library only; site is just website-build)"

# Build/refresh NeonRoot palm-docs image (Tailwind + uv; host Node optional).
docs-image:
    #!/usr/bin/env bash
    set -euo pipefail
    mkdir -p .neonroot
    neonroot vault add palm-docs "$PWD/.neonroot" 2>/dev/null || true
    neonroot image create palm-docs --template minimal --vault palm-docs 2>/dev/null || true
    cp ci/Containerfile.docs .neonroot/images/palm-docs/Containerfile
    neonroot image build palm-docs --vault palm-docs
    echo "✅ palm-docs image built — now: just website-css-sandbox | docs-build-sandbox"

# Tailwind via palm-docs image → website/styles/output.css
website-css-sandbox:
    #!/usr/bin/env bash
    set -euo pipefail
    site="$PWD/website"
    test -f "$site/styles/input.css" || { echo "error: missing website/styles/input.css" >&2; exit 1; }
    neonroot spawn palm-website-css \
        --image palm-docs --vault palm-docs --sandbox \
        --seed "$site" --seed-mode copy \
        --output "$site/styles/output.css:styles/output.css" \
        -- \
        sh -c 'export NODE_PATH="$(npm root -g)${NODE_PATH:+:$NODE_PATH}"; tailwindcss -i styles/input.css -o styles/output.css'
    echo "✅ website/styles/output.css rebuilt via palm-docs"

docs-css-sandbox: website-css-sandbox

website-css-bind:
    #!/usr/bin/env bash
    set -euo pipefail
    site="$PWD/website"
    test -f "$site/styles/input.css" || { echo "error: missing website/styles/input.css" >&2; exit 1; }
    neonroot spawn palm-website-css-bind \
        --image palm-docs --vault palm-docs --sandbox \
        --seed "$site" --seed-mode bind \
        -- \
        sh -c 'export NODE_PATH="$(npm root -g)${NODE_PATH:+:$NODE_PATH}"; tailwindcss -i styles/input.css -o styles/output.css'
    echo "✅ website/styles/output.css via palm-docs bind"

docs-css-bind: website-css-bind

# Library build in NeonRoot — git-archive seed + export docs/_build only.
docs-build-sandbox:
    #!/usr/bin/env bash
    set -euo pipefail
    seed="$(mktemp -d)"
    trap 'rm -rf "$seed"' EXIT
    git archive HEAD | tar -x -C "$seed"
    mkdir -p "$PWD/docs/_build"
    neonroot spawn palm-docs-build \
        --image palm-docs --vault palm-docs --sandbox \
        --seed "$seed" \
        --output "$PWD/docs/_build:docs/_build" \
        -- \
        uv run python scripts/docs_build.py
    echo "✅ docs/_build exported from palm-docs (library only)"

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

# -----------------------------------------------------------------------------
# 8a. CI gate (PD-001) — runs the full green suite; mypy is report-only (PD-005/T2)
# -----------------------------------------------------------------------------
# The canonical CI check. Runs WITH cli+mcp extras (matches the green baseline).
ci:
    uv run {{ci_flags}} ruff check src/palm/ tests/ examples/
    uv run {{ci_flags}} python scripts/guard_core.py
    uv run {{ci_flags}} python scripts/guard_deferred.py
    uv run {{ci_flags}} pytest -q --cov=src/palm --cov-report=term
    @echo "── mypy (report-only, non-blocking — see TECH-DEBT PD-005 / T2) ──"
    uv run {{ci_flags}} mypy src/palm/ || echo "⚠  mypy not clean yet (report-only)"

# Build/refresh the local NeonRoot palm-ci image from ci/Containerfile (one-time / on tool bumps).
ci-image:
    #!/usr/bin/env bash
    set -euo pipefail
    mkdir -p .neonroot
    neonroot vault add palm-ci "$PWD/.neonroot" 2>/dev/null || true
    neonroot image create palm-ci --template minimal --vault palm-ci 2>/dev/null || true
    cp ci/Containerfile .neonroot/images/palm-ci/Containerfile
    neonroot image build palm-ci --vault palm-ci
    echo "✅ palm-ci image built — now run: just ci-sandbox"

# Hermetic CI in a NeonRoot sandbox — seeds ONLY git-tracked files (no stale data/ or .venv).
ci-sandbox:
    #!/usr/bin/env bash
    set -euo pipefail
    seed="$(mktemp -d)"
    trap 'rm -rf "$seed"' EXIT
    git archive HEAD | tar -x -C "$seed"
    neonroot spawn palm-ci-run --image palm-ci --vault palm-ci --sandbox --seed "$seed" -- just ci
    echo "✅ hermetic CI passed in a NeonRoot sandbox"

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
    @echo "   just guard-system     → palm.system import purity + boundary tests"
    @echo "   just docs-check       → Version + documentation surface consistency"
    @echo "   just website-css      → Tailwind for website/styles (host Node)"
    @echo "   just website-build    → Assemble website/dist (Cloudflare assets)"
    @echo "   just website-build-all→ website-css + website-build"
    @echo "   just website-css-sandbox → Tailwind via palm-docs image"
    @echo "   just docs-image       → Build NeonRoot palm-docs image"
    @echo "   just docs-build       → Living Library → docs/_build (no website)"
    @echo "   just docs-build-all   → docs-css + docs-build"
    @echo "   just docs-build-sandbox → hermetic docs-build via palm-docs image"
    @echo "   just release-prep     → docs-check + full-check + build"
    @echo "   just demo-full        → examples/full_demo.py"
    @echo "   just mcp-inspector    → MCP Inspector UI for palm-mcp"
    @echo "   just palm-server      → Palm HTTP API (REST backend for MCP)"
    @echo "   just docker-up        → Palm host server in Docker (./data + ./logs)"
    @echo "   just clean            → Remove data/ + tool caches"
    @echo "   just palm --help      → CLI command list"
    @echo "Run 'just --list' for full list"