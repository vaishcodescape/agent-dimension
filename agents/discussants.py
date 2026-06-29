# Discussion-panel subagents — personas that hold and defend opinions.
#
# Where the planner/worker/critic team (agents/subagents.py) *executes* a task,
# this panel *deliberates* on one. The orchestrator convenes them as a roundtable:
# each persona reads the shared discussion thread, adds its own take, and responds
# to the others. They genuinely disagree — that friction is the point.
#
# Hand-off happens through one shared file, `discussion.md`, so the agents are
# literally talking to each other through the workspace.
#
# Rename these personas or add your own; any SubAgent listed in DISCUSSANTS becomes
# available to the orchestrator automatically. Give each persona its own LLM via
# OPTIMIST_LLM_MODEL, SKEPTIC_LLM_MODEL, etc.

from __future__ import annotations

from deepagents import SubAgent

from agents.model import build_model_for_role, model_spec_for

# Shared opening every discussant gets, so they all play by the same rules.
_PANEL_RULES = (
    "You are one voice on a discussion panel. The running conversation lives in "
    "`discussion.md` in the shared workspace. ALWAYS read it first so you know "
    "what has already been said. Then APPEND your contribution (do not overwrite "
    "others) under a heading with your name, e.g. `## {name}`. Engage directly "
    "with points others made — agree, build on them, or push back by name. Stay "
    "in character. Be concise: a few sharp sentences, not an essay. End your "
    "written reply, then summarize your position in one line back to the "
    "orchestrator."
)


# The raw persona stances, kept in one place so both the orchestrator-mediated
# panel (the SubAgents below) and the direct roundtable CLI (agents/roundtable.py)
# describe each character identically. Add a persona here and it's available to
# both front-ends.
PERSONA_STANCES = {
    "optimist": (
        "You look for upside, opportunity, and what could go right. You champion "
        "ambitious bets, but you are not naive — you ground your hope in concrete "
        "reasons. You counter excessive pessimism."
    ),
    "skeptic": (
        "You hunt for risks, hidden assumptions, failure modes, and weak evidence. "
        "You ask 'what would have to be true?' and 'how could this go wrong?'. You "
        "are rigorous, not cynical — you grant good points when they are made."
    ),
    "pragmatist": (
        "You care about what is actually feasible and what to do next. You weigh "
        "tradeoffs, cost, and effort, and you push the panel toward a concrete, "
        "actionable recommendation rather than abstract debate."
    ),
}


def persona_model_spec(name: str) -> str:
    # Model spec for a roundtable persona (used by discuss.py direct loop).
    return model_spec_for(name)


def _persona(name: str, stance: str) -> SubAgent:
    return SubAgent(
        name=name,
        description=(
            f"Discussion-panel persona ({stance}). Delegate here during a "
            "roundtable to get this viewpoint on the topic. Reads and appends to "
            "discussion.md."
        ),
        system_prompt=_PANEL_RULES.format(name=name.capitalize()) + f"\n\nYour persona: {stance}",
        model=build_model_for_role(name),
    )


OPTIMIST = _persona("optimist", PERSONA_STANCES["optimist"])
SKEPTIC = _persona("skeptic", PERSONA_STANCES["skeptic"])
PRAGMATIST = _persona("pragmatist", PERSONA_STANCES["pragmatist"])

DISCUSSANTS = [OPTIMIST, SKEPTIC, PRAGMATIST]
