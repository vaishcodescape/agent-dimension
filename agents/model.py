"""Claude model construction.

`ChatAnthropic` wraps the official Anthropic SDK, so every agent in this
sandbox talks to Claude through `/v1/messages`. We default to Claude Opus 4.8
with adaptive thinking — Claude decides how much to think per step, which is a
good fit for the open-ended, tool-calling loops these agents run.
"""

from __future__ import annotations

import os

from langchain_anthropic import ChatAnthropic

# Opus 4.8 is the most capable Opus-tier model. Override via the CLAUDE_MODEL
# env var (e.g. claude-sonnet-4-6 for cheaper/faster subagents).
DEFAULT_MODEL = "claude-opus-4-8"


def build_model(
    model: str | None = None,
    max_tokens: int = 16_000,
    thinking: bool = True,
) -> ChatAnthropic:
    """Build a Claude chat model for an agent.

    Args:
        model: Model id. Defaults to $CLAUDE_MODEL, else DEFAULT_MODEL.
        max_tokens: Output token ceiling per turn.
        thinking: Enable adaptive thinking (recommended for agentic loops).
    """
    model_id = model or os.environ.get("CLAUDE_MODEL", DEFAULT_MODEL)

    kwargs: dict = {"model": model_id, "max_tokens": max_tokens}
    if thinking:
        # Adaptive: Claude decides when/how much to think. No fixed budget to tune.
        kwargs["thinking"] = {"type": "adaptive"}

    return ChatAnthropic(**kwargs)
