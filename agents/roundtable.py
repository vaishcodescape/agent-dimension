# Direct agent-to-agent roundtable: personas converse turn by turn.
#
# Where the orchestrator panel (agents/discussants.py + the `task` tool) routes
# every turn through a coordinator, this module is a plain Python loop that calls
# each persona directly. There is no orchestrator in the middle — the agents talk
# to each other through a transcript this loop maintains, and you watch each turn
# stream in live.
#
# The conversation is autonomous: you set the topic, and the panel debates it for
# a few rounds — each agent reads everything said so far and replies to it.

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from langchain_core.messages import HumanMessage, SystemMessage

from agents.discussants import PERSONA_STANCES, persona_model_spec
from agents.model import build_model, collect_credentials_errors

# Default speaking order for a round. Any key in PERSONA_STANCES works.
DEFAULT_PANEL = ["optimist", "skeptic", "pragmatist"]

_ROUNDTABLE_RULES = (
    "You are {name}, one voice on a live discussion panel of AI agents debating a "
    "topic together. Below is the running transcript of everything said so far. "
    "Engage directly with the others — agree, build on a point, or push back, and "
    "name who you're responding to. Do NOT repeat points already made. Stay in "
    "character. Be concise: a few sharp sentences, not an essay. Speak in the "
    "first person and do NOT prefix your reply with your own name."
)


@dataclass
class Turn:
    # One contribution to the roundtable.
    speaker: str
    text: str


@dataclass
class Roundtable:
    # A direct, turn-by-turn debate among persona agents.
    #
    # Args:
    #     topic: The question the panel debates.
    #     panel: Persona names (keys of PERSONA_STANCES) in speaking order.
    #     rounds: How many times each persona speaks.
    #     model_kwargs: Forwarded to build_model (e.g. model=, thinking=).

    topic: str
    panel: list[str] = field(default_factory=lambda: list(DEFAULT_PANEL))
    rounds: int = 2
    model_kwargs: dict = field(default_factory=dict)
    transcript: list[Turn] = field(default_factory=list, init=False)
    _models: dict[str, object] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        unknown = [p for p in self.panel if p not in PERSONA_STANCES]
        if unknown:
            raise ValueError(
                f"Unknown persona(s): {', '.join(unknown)}. "
                f"Available: {', '.join(PERSONA_STANCES)}"
            )

    def _model_for(self, speaker: str):
        if speaker not in self._models:
            spec = persona_model_spec(speaker)
            kwargs = dict(self.model_kwargs)
            kwargs.setdefault("model", spec)
            self._models[speaker] = build_model(**kwargs)
        return self._models[speaker]

    def speakers(self) -> Iterable[str]:
        # Yield the speaker order for the whole session.
        for _ in range(self.rounds):
            yield from self.panel

    def turn(self, speaker: str) -> Turn:
        # Run one speaker's turn and append it to the transcript.
        chunks = list(self._stream_turn(speaker))
        text = "".join(chunks).strip()
        turn = Turn(speaker, text)
        self.transcript.append(turn)
        return turn

    def stream_turn(self, speaker: str):
        # Stream one speaker's turn token-by-token, then record it.
        #
        # Yields text deltas as they arrive; appends the finished Turn to the
        # transcript once the stream completes.
        buf: list[str] = []
        for delta in self._stream_turn(speaker):
            buf.append(delta)
            yield delta
        self.transcript.append(Turn(speaker, "".join(buf).strip()))

    # -- internals -------------------------------------------------------

    def _stream_turn(self, speaker: str):
        system, human = self._prompt_for(speaker)
        for chunk in self._model_for(speaker).stream([system, human]):
            yield _text(chunk.content)

    def _prompt_for(self, speaker: str) -> tuple[SystemMessage, HumanMessage]:
        rules = _ROUNDTABLE_RULES.format(name=speaker.capitalize())
        system = SystemMessage(rules + f"\n\nYour persona: {PERSONA_STANCES[speaker]}")
        ask = f"You are {speaker.capitalize()}. Add the next turn to the discussion."
        human = HumanMessage(self._render() + "\n\n" + ask)
        return system, human

    def _render(self) -> str:
        lines = [f"TOPIC: {self.topic}", "", "TRANSCRIPT SO FAR:"]
        if not self.transcript:
            lines.append("(nothing yet — you're opening the discussion)")
        for t in self.transcript:
            lines.append(f"\n{t.speaker.capitalize()}: {t.text}")
        return "\n".join(lines)


def _text(content) -> str:
    # Extract plain text from a message/chunk content (str or block list).
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    parts.append(block.get("text", ""))
            else:
                parts.append(str(block))
        return "".join(parts)
    return ""
