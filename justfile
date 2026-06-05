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
    uv sync --group dev
    uv run pre-commit install
    @echo "✅ Environment synced + pre-commit installed"

hygiene:
    just format
    just lint-fix

# -----------------------------------------------------------------------------
# 2. Quality & Checking (the most used group)
# -----------------------------------------------------------------------------
check: lint typecheck test-quick

full-check: format lint typecheck test-full audit guard-core

lint:
    uv run ruff check palm/ tests/

lint-fix:
    uv run ruff check --fix palm/ tests/

format:
    uv run ruff format palm/ tests/

typecheck:
    uv run mypy palm/

test-quick:
    uv run pytest -q --tb=no

test-full:
    uv run pytest --cov=palm --cov-report=term-missing

test-watch:
    uv run ptw

# -----------------------------------------------------------------------------
# 3. Refactoring & Maintenance
# -----------------------------------------------------------------------------
refactor:
    @echo "🔍 Finding dead code..."
    uv run vulture palm/ --min-confidence 70
    @echo "🧹 Running autofixes..."
    just lint-fix
    uv run autoflake --remove-all-unused-imports --in-place --recursive palm/
    @echo "📊 Complexity report:"
    uv run radon cc palm/core/ --min C
    @echo "✅ Refactor pass done. Now run 'just full-check' and review."

# -----------------------------------------------------------------------------
# 4. Palm Architecture Guards (Critical for this project)
# -----------------------------------------------------------------------------
guard-core:
    @echo "🔒 Checking Core Purity Rules (0.4.0-dev)..."
    uv run python -c '
import sys
from pathlib import Path
core = Path("palm/core")
forbidden = ("patterns", "providers", "storages", "runtimes", "definitions", "utils")
violations = []
for py in core.rglob("*.py"):
    for line in py.read_text().splitlines():
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
    uv run bandit -r palm/ -ll -ii
    uv run pip-audit

complexity:
    uv run radon cc palm/core/ -a
    uv run xenon --max-average A --max-modules B palm/

deps:
    uv pip compile pyproject.toml --output-file=requirements.txt --quiet
    @echo "✅ Dependency audit complete"

# -----------------------------------------------------------------------------
# 6. Convenience & CI-friendly
# -----------------------------------------------------------------------------
prepr: full-check   # Pre-PR / Pre-merge
    @echo "🎉 All quality gates passed — ready for review!"

clean:
    rm -rf .pytest_cache .ruff_cache .mypy_cache __pycache__ *.db
    @echo "🧼 Cleaned temporary files"

# -----------------------------------------------------------------------------
# Help & Discovery
# -----------------------------------------------------------------------------
help:
    @echo "🌴 Palm Tooling Commands:"
    @echo "   just dev          → Full setup + hygiene"
    @echo "   just check        → Fast quality check"
    @echo "   just full-check   → Everything"
    @echo "   just refactor     → Dead code + autofix"
    @echo "   just guard-core   → Architecture enforcement"
    @echo "   just audit        → Security + complexity"
    @echo "Run 'just --list' for full list"
