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

from palm.cli.solid.repl import PalmREPL
from palm.config.settings import settings
from palm.core.orchestrator import Orchestrator
from palm.core.wizard.engine import WizardEngine
from palm.utils.logging import configure_logging, logger


def main() -> None:
    console = Console()

    # Set up beautiful logging early
    configure_logging(level=settings.log_level, console=console)

    console.print("[bold green]🌴 Palm Orchestration Engine[/] - Solid Admin CLI v0.2.2")
    console.print("Type [bold]help[/] for available commands. [dim]Ctrl+D or 'exit' to quit.[/]\n")

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
    """Load the basic flat example + the rich 0.2.1 hierarchical demo."""
    try:
        from wizards.examples.create_ape_profile import (
            COMMIT_HANDLERS as BASIC_HANDLERS,
            create_ape_profile_wizard,
        )
        basic = create_ape_profile_wizard()
        engine.register(basic, commit_handlers=BASIC_HANDLERS)
        console.print("[dim]Loaded example: create_ape_profile (basic/flat)[/]")
    except Exception as exc:
        logger.debug(f"Could not load basic example: {exc}")

    try:
        from wizards.examples.onboard_new_ape import (
            COMMIT_HANDLERS as HIERARCHICAL_HANDLERS,
            onboard_new_ape_wizard,
        )
        hier = onboard_new_ape_wizard()
        engine.register(hier, commit_handlers=HIERARCHICAL_HANDLERS)
        console.print("[dim]Loaded example: onboard_new_ape (hierarchical demo)[/]")
    except Exception as exc:
        console.print(f"[dim yellow]Could not load hierarchical example: {exc}[/]")
        logger.debug(f"Hierarchical example load failed: {exc}")


if __name__ == "__main__":
    main()
