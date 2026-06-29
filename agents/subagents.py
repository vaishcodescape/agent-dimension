# Spawning subagents in the sandbox environment.

from __future__ import annotations

from deepagents import SubAgent

from agents.model import build_model_for_role
from agents.tools import EXAMPLE_TOOLS

# A "planner" that breaks a task down and writes a plan to the shared filesystem.
PLANNER = SubAgent(
    name="planner",
    description=(
        "Breaks an open-ended task into concrete steps. Delegate here first "
        "when a task is ambiguous or multi-step. Writes plan.md to the workspace."
    ),
    system_prompt=(
        "You are the Planner. Given a task, produce a short, ordered plan of "
        "concrete steps. Write the plan to `plan.md` using the file tools, then "
        "summarize it in your reply. Do not try to execute the steps yourself."
    ),
    model=build_model_for_role("planner"),
)

# A "worker" that does the actual work, using the example tools.
WORKER = SubAgent(
    name="worker",
    description=(
        "Executes a single, well-specified step. Delegate one concrete unit of "
        "work at a time. Can read/write workspace files, run shell commands via "
        "execute, and use example tools."
    ),
    system_prompt=(
        "You are the Worker. You are given one concrete step. Do exactly that "
        "step — no more. Read any inputs you need from the workspace with the "
        "file tools, run shell commands with execute when needed (git, curl, "
        "python, pip, make, etc.), and write your output to a clearly named file. "
        "Report what you produced and where you saved it."
    ),
    tools=EXAMPLE_TOOLS,
    # Override via WORKER_LLM_MODEL (e.g. openai:gpt-4.1-mini for cheaper grunt work).
    model=build_model_for_role("worker"),
)

# A "critic" that reviews work and pushes back.
CRITIC = SubAgent(
    name="critic",
    description=(
        "Reviews work products for correctness and completeness against the "
        "original task. Delegate here before declaring a task done."
    ),
    system_prompt=(
        "You are the Critic. Read the relevant workspace files and the original "
        "task. Identify concrete problems, gaps, or errors. Be specific and "
        "actionable. If the work is solid, say so plainly — don't invent issues."
    ),
    model=build_model_for_role("critic"),
)

# The task-execution team: decompose → do → review.
TASK_SUBAGENTS = [PLANNER, WORKER, CRITIC]

# The full roster the orchestrator can delegate to = the task team plus the
# discussion panel (personas that deliberate and disagree). Importing here keeps
# orchestrator.py simple — it just consumes SUBAGENTS.
from agents.discussants import DISCUSSANTS  # noqa: E402  (after task team is defined)

SUBAGENTS = [*TASK_SUBAGENTS, *DISCUSSANTS]
