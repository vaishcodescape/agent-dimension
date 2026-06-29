# A multi-agent sandbox built on the deepagents framework.
#
# An orchestrator agent delegates to specialized subagents, all sharing a
# virtual filesystem and a todo planner (provided by deepagents). Each agent
# can run on a different LLM provider.

from agents.model import (
    build_model,
    build_model_for_role,
    collect_credentials_errors,
    default_model_spec,
    missing_credentials_message,
    model_spec_for,
    normalize_model_spec,
)
from agents.orchestrator import build_orchestrator
from agents.providers import PROVIDERS, example_specs, supported_providers

__all__ = [
    "PROVIDERS",
    "build_model",
    "build_model_for_role",
    "build_orchestrator",
    "collect_credentials_errors",
    "default_model_spec",
    "example_specs",
    "missing_credentials_message",
    "model_spec_for",
    "normalize_model_spec",
    "supported_providers",
]
