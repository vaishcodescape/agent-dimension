# agent-sandbox

A multi-agent sandbox where agents interact with each other, built on the
[**deepagents**](https://pypi.org/project/deepagents/) framework and **Claude**
(via the Anthropic API).

## Architecture

An **orchestrator** agent delegates to specialized **subagents** through
deepagents' built-in `task` tool. All agents share a virtual filesystem and a
todo planner, so they coordinate by reading and writing files in a common
workspace.

```
orchestrator
  task team — get something DONE:
  ├─ task → planner   (breaks the task into steps, writes plan.md)
  ├─ task → worker    (executes one step at a time, uses example tools)
  └─ task → critic    (reviews the work before it's declared done)
  discussion panel — DELIBERATE an open question:
  ├─ task → optimist     (argues the upside)
  ├─ task → skeptic      (argues the risks)
  └─ task → pragmatist   (weighs tradeoffs, pushes to a decision)
        shared virtual filesystem + todo planner
```

The panel agents talk *to each other* by reading and appending to a shared
`discussion.md`, so they respond to one another across rounds, and the
orchestrator distills the bottom line.

Claude is the model behind every agent: `langchain-anthropic`'s `ChatAnthropic`
wraps the official Anthropic SDK, so each agent talks to Claude through
`/v1/messages`. Default model: **Claude Opus 4.8** with adaptive thinking.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env        # then add your ANTHROPIC_API_KEY to .env
```

## Chat with the agents

For an ongoing conversation — where the orchestrator remembers earlier turns and
the files the team wrote — use the interactive chat:

```bash
python chat.py
```

Then just talk to it. It answers simple turns itself, convenes the task team for
real work, or convenes the discussion panel when you ask the agents to weigh in:

```
you › Should we rewrite the service in Rust? Have the panel debate it.
```

The optimist, skeptic, and pragmatist take turns in `discussion.md`, argue with
each other, and the orchestrator wraps up with a balanced bottom line.

In-chat commands: `/files` (show the workspace), `/reset` (fresh conversation),
`/help`, `/quit`.

## Watch the agents debate (roundtable)

For a focused **agent-to-agent debate** with no orchestrator in the middle, use
the roundtable CLI. You give a topic and watch the agents talk *directly* to
each other, turn by turn, streamed live with a colored label per speaker:

```bash
python discuss.py "Should we ship the beta this week?"
python discuss.py --rounds 3 "Monorepo or polyrepo?"
python discuss.py --panel optimist,skeptic "Is the deadline realistic?"
```

Each agent reads the running transcript and responds to the others by name.
Options: `--rounds N` (turns per agent, default 2), `--panel a,b,c` (speaking
order). With no topic argument it prompts for one.

Unlike the panel inside `chat.py`, this loop is plain Python (`agents/roundtable.py`)
that calls each persona directly — it shares the persona definitions, but skips
the orchestrator and the shared filesystem.

## Run a one-shot task

When you just want a single task run and then exit:

```bash
python run.py "Draft a one-paragraph project pitch, have it critiqued, and save the final version to pitch.md"
```

With no argument it runs a built-in demo task. The CLI streams what each agent
does — messages, tool calls, and delegations — and prints the shared workspace
files at the end.

## Project layout

| Path | What it is |
|------|------------|
| `agents/model.py` | Builds the Claude model (default `claude-opus-4-8`, adaptive thinking). |
| `agents/tools.py` | Example custom `@tool`s. Replace the stubs with real logic. |
| `agents/subagents.py` | The `planner` / `worker` / `critic` task team. |
| `agents/discussants.py` | The `optimist` / `skeptic` / `pragmatist` discussion panel. |
| `agents/orchestrator.py` | Assembles the orchestrator + its full subagent team. |
| `agents/roundtable.py` | Direct turn-by-turn debate engine (no orchestrator). |
| `agents/render.py` | Shared transcript-rendering helpers for the CLIs. |
| `chat.py` | Interactive chat with memory across turns. |
| `discuss.py` | Roundtable CLI: agents debate a topic directly, streamed live. |
| `run.py` | One-shot CLI: runs a single task and streams the result. |

## Customizing it

This is a **generic skeleton**. To adapt it to your use case:

- **Add agents:** define more `SubAgent`s in `agents/subagents.py` and they
  become available to the orchestrator automatically.
- **Add tools:** write `@tool` functions in `agents/tools.py` and attach them to
  a subagent's `tools` list.
- **Tune cost:** give subagents a cheaper model (e.g. `claude-sonnet-4-6` or
  `claude-haiku-4-5`) via the `model` field on `SubAgent`, keeping the
  orchestrator on Opus.
- **Rewrite the prompts:** the roles and `system_prompt`s are placeholders —
  make them specific to your domain.
