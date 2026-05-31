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
    uv run ruff check src/ tests/

lint-fix:
    uv run ruff check --fix src/ tests/

format:
    uv run ruff format src/ tests/

typecheck:
    uv run mypy src/
    uv run pyright src/

test-quick:
    uv run pytest -q --tb=no

test-full:
    uv run pytest --cov=src/palm --cov-report=term-missing

test-watch:
    uv run ptw

# -----------------------------------------------------------------------------
# 3. Refactoring & Maintenance
# -----------------------------------------------------------------------------
refactor:
    @echo "🔍 Finding dead code..."
    uv run vulture src/ --min-confidence 70
    @echo "🧹 Running autofixes..."
    just lint-fix
    uv run autoflake --remove-all-unused-imports --in-place --recursive src/
    @echo "📊 Complexity report:"
    uv run radon cc src/palm/core/ --min C
    @echo "✅ Refactor pass done. Now run 'just full-check' and review."

# -----------------------------------------------------------------------------
# 4. Palm Architecture Guards (Critical for this project)
# -----------------------------------------------------------------------------
guard-core:
    @echo "🔒 Checking Core Purity Rules (0.3.0-dev)..."
    uv run python -c '
import sys
from pathlib import Path
src = Path("src")
violations = []
for py in src.rglob("*.py"):
    content = py.read_text()
    if "palm.cli.solid.legacy" in content and "cli/solid/legacy" not in str(py):
        violations.append(f"Legacy import in core: {py}")
    if "behavior_tree" in content and "orchestration" in str(py):
        violations.append(f"BT import in orchestration: {py}")
if violations:
    print("\n".join(violations))
    sys.exit(1)
else:
    print("✅ Core architecture rules respected")
    '

guard-legacy:
    @echo "📌 Legacy package is reference-only — no new features here"

# -----------------------------------------------------------------------------
# 5. Audit & Security
# -----------------------------------------------------------------------------
audit: security complexity deps

security:
    uv run bandit -r src/ -ll -ii
    uv run pip-audit

complexity:
    uv run radon cc src/palm/core/ -a
    uv run xenon --max-average A --max-modules B src/

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
