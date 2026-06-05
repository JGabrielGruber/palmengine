"""
Entry point for the Palm Solid Admin CLI.

Usage:
    palm
    python -m palm.cli.solid
    python main.py
"""

from __future__ import annotations

import sys

from rich.console import Console

from palm.cli.solid.legacy.orchestrator import Orchestrator
from palm.cli.solid.legacy.wizard.engine import WizardEngine
from palm.cli.solid.repl import PalmREPL
from palm.config.settings import settings
from palm.utils.logging import configure_logging, logger


def main() -> None:
    legacy_mode = "--legacy" in sys.argv
    if legacy_mode:
        sys.argv.remove("--legacy")

    console = Console()

    # Set up beautiful logging early
    configure_logging(level=settings.log_level, console=console)

    banner = "[bold green]🌴 Palm Orchestration Engine[/] - Solid Admin CLI v0.3.0-dev"
    if legacy_mode:
        banner += " [yellow](legacy mode)[/]"
    console.print(banner)
    console.print("Type [bold]help[/] for available commands. [dim]Ctrl+D or 'exit' to quit.[/]\n")

    if legacy_mode:
        console.print(
            "[yellow]⚠️  Running on the legacy (pre-clean-core) implementation. This path will change in a future release.[/]\n"
        )

    logger.info("Starting Palm Solid Admin CLI")

    # Create a fresh orchestrator + engine for this CLI session
    orchestrator = Orchestrator()
    engine: WizardEngine = orchestrator.wizard_engine

    # Auto-register any wizards found in the wizards/ package (best effort)
    _auto_register_example_wizards(engine, console)

    repl = PalmREPL(orchestrator=orchestrator, engine=engine, console=console)
    try:
        repl.run()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted. Goodbye.[/]")
        logger.info("CLI interrupted by user")
        sys.exit(0)


def _auto_register_example_wizards(engine: WizardEngine, console: Console) -> None:
    """Try to load the built-in example wizard(s) + their commit handlers."""
    try:
        from wizards.examples.create_ape_profile import (
            COMMIT_HANDLERS,
            create_ape_profile_wizard,
        )

        wizard_def = create_ape_profile_wizard()
        engine.register(wizard_def, commit_handlers=COMMIT_HANDLERS)
        console.print("[dim]Loaded example wizard: create_ape_profile (with commit handler)[/]")
    except Exception as exc:
        console.print(f"[dim yellow]Could not auto-load example wizards: {exc}[/]")
        logger.debug(f"Wizard auto-load failed: {exc}")


if __name__ == "__main__":
    main()
