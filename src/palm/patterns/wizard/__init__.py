"""
Wizard pattern app — interactive multi-step flows with backtracking and events.

Self-contained subpackage:

- ``pattern.py`` — ``WizardPattern`` implementation
- ``handler.py`` — commit handler registry
- ``builder.py`` / ``options.py`` — definition → pattern materialization
- ``registry.py`` — ``pattern_registry`` wiring
"""

from palm.patterns.wizard import registry as registry  # — side effect
from palm.patterns.wizard.builder import wizard_config_from_options
from palm.patterns.wizard.config import WizardConfig, WizardStepConfig
from palm.patterns.wizard.events import WizardEventType
from palm.patterns.wizard.handler import (
    CommitContext,
    CommitRegistry,
    CommitResult,
    default_commit_registry,
)
from palm.patterns.wizard.keys import WizardKeys
from palm.patterns.wizard.options import parse_wizard_flow_options, wizard_metadata_from_flow
from palm.patterns.wizard.pattern import WizardPattern, default_wizard_config
from palm.patterns.wizard.persistence import (
    extract_instance_fields_from_job,
    prepare_wizard_resume_state,
    wizard_runtime_position_for_job,
    wizard_step_slug_for_job,
)
from palm.patterns.wizard.schema_validation import materialize_wizard_step_schemas
from palm.patterns.wizard.state import (
    complete_step_input,
    enter_step,
    get_answers,
    leave_step,
    step_scope,
)
from palm.patterns.wizard.submission import wizard_submission_metadata
from palm.patterns.wizard.validation import (
    StepValidationRule,
    ValidationRegistry,
    default_validation_registry,
    validate_collected_answers,
    validate_step_input,
    validate_step_schema,
    validate_step_state_schema,
    validate_step_value,
)

__all__ = [
    "CommitContext",
    "CommitRegistry",
    "CommitResult",
    "StepValidationRule",
    "complete_step_input",
    "enter_step",
    "get_answers",
    "leave_step",
    "step_scope",
    "ValidationRegistry",
    "WizardConfig",
    "WizardEventType",
    "WizardKeys",
    "WizardPattern",
    "WizardStepConfig",
    "default_commit_registry",
    "default_validation_registry",
    "default_wizard_config",
    "materialize_wizard_step_schemas",
    "extract_instance_fields_from_job",
    "parse_wizard_flow_options",
    "prepare_wizard_resume_state",
    "registry",
    "validate_collected_answers",
    "validate_step_input",
    "validate_step_schema",
    "validate_step_state_schema",
    "validate_step_value",
    "wizard_config_from_options",
    "wizard_metadata_from_flow",
    "wizard_runtime_position_for_job",
    "wizard_step_slug_for_job",
    "wizard_submission_metadata",
]