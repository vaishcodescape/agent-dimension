# Example custom tools for subagents.
#
# These are deliberately generic stubs — swap their bodies for real logic
# (API calls, DB queries, shell commands, etc.) for your own use case.
#
# Note: every agent ALSO gets deepagents' built-in tools for free — a shared
# virtual filesystem (ls / read_file / write_file / edit_file) and a todo
# planner (write_todos) — so agents coordinate by reading and writing files in
# the shared workspace. You usually don't need to add file tools yourself.

from __future__ import annotations

from langchain_core.tools import tool


@tool(description="Echo the given text back. A trivial stub to confirm tool-calling works.")
def echo(text: str) -> str:
    return text


@tool(description="Count the number of whitespace-separated words in the given text.")
def word_count(text: str) -> int:
    return len(text.split())


# Tools available to subagents. Add your own @tool functions here and wire them
# into a subagent's `tools` list in agents/subagents.py.
EXAMPLE_TOOLS = [echo, word_count]
