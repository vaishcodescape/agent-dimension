#!/usr/bin/env python3
# Watch the AI agents debate a topic, turn by turn.
#
# You give a topic; the panel talks it through directly — each agent reads what
# the others have said and responds to it. There's no orchestrator in the middle:
# you set the topic and watch the agents talk to each other.
#
# Usage:
#     python discuss.py
#     python discuss.py "Should we ship the beta this week?"
#     python discuss.py --rounds 3 "Monorepo or polyrepo?"
#     python discuss.py --panel optimist,skeptic "Is the deadline realistic?"
#
# Options:
#     --rounds N        how many times each agent speaks (default 2)
#     --panel a,b,c     persona speaking order (default optimist,skeptic,pragmatist)

from __future__ import annotations

import argparse
import os
import sys

from dotenv import load_dotenv

# Load ANTHROPIC_API_KEY (and optional CLAUDE_MODEL) before the client loads.
load_dotenv()

from agents.discussants import PERSONA_STANCES, persona_model_spec
from agents.model import collect_credentials_errors
from agents.roundtable import DEFAULT_PANEL, Roundtable

# Distinct colors per speaker so turns are easy to tell apart in the terminal.
_COLORS = ["36", "33", "35", "32", "34", "31"]  # cyan, yellow, magenta, green, blue, red
_RESET = "\033[0m"
_DIM = "\033[2m"

LABEL_WIDTH = 12


def _use_color() -> bool:
    return sys.stdout.isatty() and os.environ.get("NO_COLOR") is None


def _color_for(name: str, panel: list[str]) -> str:
    idx = panel.index(name) if name in panel else len(panel)
    return _COLORS[idx % len(_COLORS)]


def _label(name: str, panel: list[str], color: bool) -> str:
    tag = f"[{name}]".ljust(LABEL_WIDTH)
    if not color:
        return tag
    return f"\033[{_color_for(name, panel)}m{tag}{_RESET}"


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Watch the AI agents debate a topic, turn by turn.",
    )
    p.add_argument("topic", nargs="*", help="the question for the panel to debate")
    p.add_argument("--rounds", type=int, default=2, help="turns per agent (default 2)")
    p.add_argument(
        "--panel",
        default=",".join(DEFAULT_PANEL),
        help="comma-separated persona order (default: %(default)s)",
    )
    return p.parse_args(argv)


def main(argv: list[str]) -> int:
    args = _parse_args(argv)

    panel = [p.strip() for p in args.panel.split(",") if p.strip()]
    unknown = [p for p in panel if p not in PERSONA_STANCES]
    if unknown:
        print(
            f"Unknown persona(s): {', '.join(unknown)}\n"
            f"Available: {', '.join(PERSONA_STANCES)}",
            file=sys.stderr,
        )
        return 1

    if err := collect_credentials_errors(*(persona_model_spec(p) for p in panel)):
        print(err, file=sys.stderr)
        return 1

    topic = " ".join(args.topic).strip()
    if not topic:
        try:
            topic = input("topic › ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nbye.")
            return 0
    if not topic:
        print("No topic given.", file=sys.stderr)
        return 1

    table = Roundtable(
        topic=topic,
        panel=panel,
        rounds=args.rounds,
    )

    color = _use_color()
    print(f"\n{_DIM if color else ''}=== ROUNDTABLE ==={_RESET if color else ''}")
    print(f"topic: {topic}")
    print(f"panel: {' → '.join(panel)}  ({args.rounds} rounds)\n")

    indent = " " * LABEL_WIDTH
    try:
        for speaker in table.speakers():
            sys.stdout.write(_label(speaker, panel, color) + " ")
            sys.stdout.flush()
            at_line_start = False
            for delta in table.stream_turn(speaker):
                # Keep wrapped lines aligned under the label.
                text = delta.replace("\n", "\n" + indent)
                if at_line_start:
                    text = text.lstrip()
                    at_line_start = False
                sys.stdout.write(text)
                sys.stdout.flush()
            print("\n")
    except KeyboardInterrupt:
        print("\n  (stopped)")
        return 0

    print(f"{_DIM if color else ''}=== DONE ==={_RESET if color else ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
