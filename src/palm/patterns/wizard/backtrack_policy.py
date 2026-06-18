"""
Wizard backtrack policy — which steps may be rewound.
"""

from __future__ import annotations

from palm.patterns.wizard.config import WizardConfig


def can_backtrack_to(config: WizardConfig, target: str | int) -> bool:
    """Return whether backtracking to ``target`` (slug or index) is allowed."""
    if not config.allow_backtrack:
        return False

    slug = target if isinstance(target, str) else config.iter_tree_steps()[target].slug
    if slug in config.protected_slugs():
        return False

    step = config.get_step(slug)
    if step is not None and step.is_protected:
        return False
    return True