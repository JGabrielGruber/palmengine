# =============================================================================
# Palm Orchestration Engine — Justfile
# Run `just --list` to see all commands
# Highly structured, discoverable, and terminal-first.
# =============================================================================

set dotenv-load
set export

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
    uv run pre-commit install
    @echo "✅ Environment synced (dev + cli extras) + pre-commit installed"

hygiene:
    just format
    just lint-fix

# -----------------------------------------------------------------------------
# 2. Quality & Checking (the most used group)
# -----------------------------------------------------------------------------
check: lint typecheck test-quick guard-core

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
    uv run python -c '
import sys
from pathlib import Path
core = Path("src/palm/core")
forbidden = ("patterns", "providers", "storages", "runtimes", "definitions", "common", "executions", "utils")
forbidden_test_artifacts = ("TestMode", "TestRunner", "StubInteractiveLeaf")
violations = []
for py in core.rglob("*.py"):
    if py.name.startswith("test_"):
        violations.append(f"test module in core: {py}")
    text = py.read_text()
    for name in forbidden_test_artifacts:
        if f"class {name}" in text:
            violations.append(f"{py}: forbidden test class {name}")
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("from palm.") and not stripped.startswith("import palm."):
            continue
        for pkg in forbidden:
            if f"palm.{pkg}" in stripped:
                violations.append(f"{py}: {stripped}")
if violations:
    print("Core purity violations:")
    print("\n".join(violations))
    sys.exit(1)
print("✅ Core architecture rules respected")
'

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
# 6. Palm CLI (requires --extra cli)
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

demo-full:
    uv run python examples/full_demo.py

# -----------------------------------------------------------------------------
# 7. Convenience & CI-friendly
# -----------------------------------------------------------------------------
prepr: full-check
    @echo "🎉 Palm 0.6.0 quality gates passed — ready for release review!"

clean:
    rm -rf .pytest_cache .ruff_cache .mypy_cache __pycache__ *.db
    @echo "🧼 Cleaned temporary files"

# -----------------------------------------------------------------------------
# Help & Discovery
# -----------------------------------------------------------------------------
help:
    @echo "🌴 Palm Tooling Commands:"
    @echo "   just dev              → Full setup + hygiene"
    @echo "   just check            → Fast quality check + guard-core"
    @echo "   just test-core        → Pure palm.core contract tests"
    @echo "   just full-check       → Everything + demo-full"
    @echo "   just prepr            → Pre-release gate (0.6.0)"
    @echo "   just demo-full        → examples/full_demo.py"
    @echo "   just palm --help      → CLI command list"
    @echo "   just palm-version     → palm version --full"
    @echo "   just palm-doctor      → CLI health + examples"
    @echo "   just palm-repl        → Interactive Palm shell"
    @echo "Run 'just --list' for full list"