#!/usr/bin/env python3
# Interactive chat with the multi-agent sandbox.
#
# Unlike run.py (one task, then exit), this opens an ongoing conversation. The
# orchestrator remembers the whole session — earlier turns, the files the team
# wrote — so you can follow up, refine, and ask the panel to debate things.
#
# Usage:
#     python chat.py
#
# Type a message and press enter. The orchestrator answers directly for simple
# turns, convenes the planner/worker/critic team for real tasks, or convenes the
# discussion panel (optimist / skeptic / pragmatist) when you ask the agents to
# weigh in on something.
#
# Commands:
#     /files   show the shared workspace files
#     /reset   start a fresh conversation (clears memory + workspace)
#     /help    show these commands
#     /quit    exit (also: /exit, Ctrl-D)

from __future__ import annotations

import sys
import uuid

from dotenv import load_dotenv

# Load ANTHROPIC_API_KEY (and optional CLAUDE_MODEL) before the client loads.
load_dotenv()

from langgraph.checkpoint.memory import InMemorySaver

from agents import build_orchestrator, collect_credentials_errors, default_model_spec
from agents.render import format_message
from agents.sandbox import list_workspace_files, sandbox_enabled

HELP = """\
Interactive chat with the multi-agent sandbox.

Unlike run.py (one task, then exit), this opens an ongoing conversation. The
orchestrator remembers the whole session — earlier turns, the files the team
wrote — so you can follow up, refine, and ask the panel to debate things.

Usage:
    python chat.py

Type a message and press enter. The orchestrator answers directly for simple
turns, convenes the planner/worker/critic team for real tasks, or convenes the
discussion panel (optimist / skeptic / pragmatist) when you ask the agents to
weigh in on something.

Commands:
    /files   show the shared workspace files
    /reset   start a fresh conversation (clears memory + workspace)
    /help    show these commands
    /quit    exit (also: /exit, Ctrl-D)
"""

BANNER = """\
=== agent-sandbox chat ===
Chatting with the orchestrator + its team. It can do tasks (planner/worker/
critic) or convene a discussion panel (optimist/skeptic/pragmatist).
Type /help for commands, /quit to exit.
"""


def _print_new_messages(state: dict, seen: int) -> int:
    # Print messages we haven't shown yet; return the new running count.
    messages = state.get("messages", [])
    for msg in messages[seen:]:
        line = format_message(msg)
        if line:
            print(line)
    return len(messages)


def _show_files(agent, config) -> None:
    if sandbox_enabled():
        files = list_workspace_files()
        if not files:
            print("  (workspace is empty)")
            return
        print("\n=== WORKSPACE FILES ===")
        for name, content in files.items():
            print(f"\n--- {name} ---\n{content}")
        return

    state = agent.get_state(config)
    files = (state.values or {}).get("files", {}) or {}
    if not files:
        print("  (workspace is empty)")
        return
    print("\n=== WORKSPACE FILES ===")
    for name, content in files.items():
        body = content if isinstance(content, str) else str(content)
        print(f"\n--- {name} ---\n{body}")


def main() -> int:
    if err := collect_credentials_errors(default_model_spec()):
        print(err, file=sys.stderr)
        return 1

    # The checkpointer is what gives the conversation memory: each turn is
    # appended to the same thread_id, so the agent sees the full history.
    agent = build_orchestrator(checkpointer=InMemorySaver())
    thread_id = uuid.uuid4().hex
    config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 100}

    print(BANNER)

    while True:
        try:
            user = input("\nyou › ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nbye.")
            return 0

        if not user:
            continue

        if user in ("/quit", "/exit"):
            print("bye.")
            return 0
        if user == "/help":
            print(HELP)
            continue
        if user == "/files":
            _show_files(agent, config)
            continue
        if user == "/reset":
            thread_id = uuid.uuid4().hex
            config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 100}
            print("  (started a fresh conversation)")
            continue

        # Stream this turn. The checkpointer already holds prior turns, so we
        # only send the new user message; the agent merges it with history.
        seen = 0
        try:
            for state in agent.stream(
                {"messages": [{"role": "user", "content": user}]},
                config=config,
                stream_mode="values",
            ):
                # On the first chunk the state echoes the full history; skip
                # straight to the tail so we don't reprint past turns.
                if seen == 0:
                    seen = max(0, len(state.get("messages", [])) - 1)
                seen = _print_new_messages(state, seen)
        except KeyboardInterrupt:
            print("\n  (interrupted — your next message continues the thread)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
