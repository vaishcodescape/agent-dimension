#!/usr/bin/env python3
"""Run the multi-agent sandbox on a task.

Usage:
    python run.py "your task here"
    python run.py                      # runs a built-in demo task

Streams what each agent does (messages, tool calls, delegations) and prints the
shared workspace files at the end.
"""

from __future__ import annotations

import sys

from dotenv import load_dotenv

# Load ANTHROPIC_API_KEY (and optional CLAUDE_MODEL) from .env before anything
# touches the Anthropic client.
load_dotenv()

import os

from agents import build_orchestrator
from agents.render import format_message

DEMO_TASK = (
    "Draft a one-paragraph project pitch for a multi-agent coding assistant, "
    "have it critiqued, and save the final version to pitch.md"
)


def main() -> int:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print(
            "ANTHROPIC_API_KEY is not set.\n"
            "Copy .env.example to .env and add your key:\n"
            "    cp .env.example .env",
            file=sys.stderr,
        )
        return 1

    task = " ".join(sys.argv[1:]).strip() or DEMO_TASK
    print(f"\n=== TASK ===\n{task}\n\n=== RUN ===")

    agent = build_orchestrator()
    seen = 0
    final_state = None

    # stream_mode="values" emits the full state after each step; we print only
    # messages we haven't shown yet so the transcript reads top-to-bottom.
    for state in agent.stream(
        {"messages": [{"role": "user", "content": task}]},
        stream_mode="values",
        config={"recursion_limit": 100},
    ):
        final_state = state
        messages = state.get("messages", [])
        for msg in messages[seen:]:
            line = format_message(msg)
            if line:
                print(line)
        seen = len(messages)

    # Show the shared virtual filesystem the agents wrote to.
    files = (final_state or {}).get("files", {}) or {}
    if files:
        print("\n=== WORKSPACE FILES ===")
        for name, content in files.items():
            body = content if isinstance(content, str) else str(content)
            print(f"\n--- {name} ---\n{body}")

    print("\n=== DONE ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
