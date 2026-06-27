"""A multi-agent sandbox built on the deepagents framework + Claude.

An orchestrator agent delegates to specialized subagents, all sharing a
virtual filesystem and a todo planner (provided by deepagents).
"""

from agents.orchestrator import build_orchestrator

__all__ = ["build_orchestrator"]
