"""Shared rendering helpers for the CLI front-ends (run.py, chat.py).

Turns LangChain message objects into readable transcript lines so both the
one-shot task runner and the interactive chat show agent activity the same way.
"""

from __future__ import annotations


def format_message(msg) -> str | None:
    """Render one LangChain message as a readable line, or None to skip it."""
    role = getattr(msg, "type", "?")  # 'human' | 'ai' | 'tool'
    text = ""
    content = getattr(msg, "content", "")
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        # Anthropic content blocks: keep text, note thinking blocks.
        parts = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    parts.append(block.get("text", ""))
                elif block.get("type") == "thinking":
                    parts.append("[thinking…]")
            else:
                parts.append(str(block))
        text = " ".join(p for p in parts if p)

    tool_calls = getattr(msg, "tool_calls", None) or []
    call_strs = [f"→ {tc['name']}({short(tc.get('args', {}))})" for tc in tool_calls]

    pieces = [p for p in [text.strip(), *call_strs] if p]
    if not pieces:
        return None
    return f"  [{role}] " + "\n         ".join(pieces)


def short(args: dict, limit: int = 120) -> str:
    """Compactly render tool-call args, truncating long values."""
    s = ", ".join(f"{k}={v!r}" for k, v in args.items())
    return s if len(s) <= limit else s[:limit] + "…"
