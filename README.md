# agent-dimension

**A shared environment where AI agents can interact with eachother, and use tools together.**

agent-dimension is a multi-agent sandbox built on
**[deepagents](https://pypi.org/project/deepagents/)** and
**[LangChain](https://python.langchain.com/)**. You chat with an orchestrator;
it delegates to specialist agents that **coordinate through a common workspace** reading each other's files, replying to each other's arguments, and calling tools (shell commands, custom functions, filesystem ops) to get work done as a team.

This is not a single chatbot. It is a **room full of agents** that can:

- **Talk to you** — the orchestrator is your conversational partner; you steer,
follow up, and ask for debate or execution.
- **Talk to each other** — subagents respond to prior turns, push back by name,
and build on shared artifacts (`plan.md`, `discussion.md`, …).
- **Use tools on shared state** — one agent writes a plan, another runs shell
commands against it, a third reviews the output; all through the same workspace.
- **Run on different models** — each agent can use a different provider (OpenAI,
Anthropic, Gemini, Groq, Grok, DeepSeek, Mistral, Ollama).

In Docker, agents also get a real Linux sandbox (`execute`, `git`, `curl`, …) so
tool use is not limited to a virtual in-memory filesystem.

---



## How agents interact

Everything happens in one **shared environment** (in-memory locally, `/workspace`
in Docker). Agents do not pass private messages — they coordinate by **reading
and writing the same files** and by **delegating through the orchestrator**.

agent-dimension architecture

### Three modes of agent-to-agent conversation

1. **Task coordination** (`chat.py` / `run.py`) — planner breaks work into steps;
  worker executes one step at a time (tools + shell); critic reviews before the
   orchestrator calls it done. Agents hand off through `plan.md` and output files.
2. **Panel debate** (`chat.py`) — optimist, skeptic, and pragmatist take turns
  appending to `discussion.md`, explicitly responding to each other's points.
   The orchestrator reads the thread and reports tensions and a bottom line.
3. **Direct roundtable** (`discuss.py`) — no orchestrator in the loop. Personas
  speak turn-by-turn to each other (and about each other by name) in a live
   transcript streamed to your terminal.

---



## Quick start



### Local (Python 3.14+)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add API key(s) for the provider(s) you use
```



### Docker (shell + filesystem sandbox)

```bash
cp .env.example .env
docker compose build
docker compose run --rm chat
```

Docker auto-enables `AGENT_SANDBOX=1`: agents share `/workspace` on disk and can
run real shell commands (`git`, `python`, `make`, …). A named volume persists files
across runs.

---



## Running the sandbox



### Chat with the team (recommended)

```bash
python chat.py
```

You talk to the orchestrator; it talks to the agents. Session memory is kept across turns  follow up, refine, or ask the panel to weigh in:

```
you › Break down a migration plan, have the worker draft a checklist, then
      have the critic review it.

you › Now have the panel debate whether we should do it this quarter.
```

Commands: `/files` · `/reset` · `/help` · `/quit`

### One-shot task

```bash
python run.py "Draft a pitch, have it critiqued, save the final version to pitch.md"
```

Runs a single coordinated task, streams delegations and tool calls, prints
workspace files, then exits.

### Watch agents debate each other directly

```bash
python discuss.py "Should we ship the beta this week?"
python discuss.py --rounds 3 --panel optimist,skeptic "Monorepo or polyrepo?"
```

Each persona reads the full transcript and replies to the others by name — no
orchestrator, streamed live with colored labels.

---



## Configuration

Copy `[.env.example](.env.example)` to `.env`. It documents every variable,
defaults, and API key URLs.

```bash
cp .env.example .env
```



### Quick reference


| Variable                                   | Default                     | Purpose                                       |
| ------------------------------------------ | --------------------------- | --------------------------------------------- |
| `LLM_MODEL`                                | `anthropic:claude-opus-4-8` | Orchestrator model (`provider:model-id`)      |
| `SUBAGENT_LLM_MODEL`                       | —                           | Default model for all subagents               |
| `{ROLE}_LLM_MODEL`                         | —                           | Per-agent override (`WORKER_`, `SKEPTIC_`, …) |
| `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` / … | —                           | Keys for each provider you use                |
| `LLM_MAX_TOKENS`                           | `64000`                     | Max output tokens per turn                    |
| `AGENT_SANDBOX`                            | auto in Docker              | Real shell + disk workspace                   |
| `AGENT_WORKSPACE`                          | `/workspace`                | Sandbox working directory                     |


**Providers:** `openai`, `anthropic`, `google_genai` (alias `gemini`), `ollama`,
`deepseek`, `xai` (alias `grok`), `groq`, `mistralai` (alias `mistral`).

**Mix models per agent** — e.g. orchestrator on Claude, worker on Groq, skeptic on Grok:

```bash
LLM_MODEL=anthropic:claude-opus-4-8
WORKER_LLM_MODEL=groq:llama-3.3-70b-versatile
SKEPTIC_LLM_MODEL=xai:grok-3
```

Full reference: `[.env.example](.env.example)`

---



## Project layout


| Path                                               | Role                                                 |
| -------------------------------------------------- | ---------------------------------------------------- |
| `[agents/orchestrator.py](agents/orchestrator.py)` | Orchestrator + delegation to the full team           |
| `[agents/subagents.py](agents/subagents.py)`       | Task team: planner, worker, critic                   |
| `[agents/discussants.py](agents/discussants.py)`   | Panel personas (optimist, skeptic, pragmatist)       |
| `[agents/sandbox.py](agents/sandbox.py)`           | Docker/local shell backend (`execute`, `/workspace`) |
| `[agents/model.py](agents/model.py)`               | Multi-provider model construction                    |
| `[agents/providers.py](agents/providers.py)`       | Supported LLM providers and API keys                 |
| `[agents/tools.py](agents/tools.py)`               | Custom `@tool` stubs (attach to subagents)           |
| `[agents/roundtable.py](agents/roundtable.py)`     | Direct agent-to-agent debate loop                    |
| `[chat.py](chat.py)`                               | Interactive chat — you + orchestrator + team         |
| `[run.py](run.py)`                                 | One-shot coordinated task                            |
| `[discuss.py](discuss.py)`                         | Live roundtable (agents talk to each other only)     |


---



## For contributors



### Add an agent that talks to the team

1. Define a `SubAgent` in `[agents/subagents.py](agents/subagents.py)` or
  `[agents/discussants.py](agents/discussants.py)` with a clear `description`
   (when the orchestrator should delegate) and `system_prompt` (how it interacts
   with shared files and other agents' output).
2. Add it to `SUBAGENTS`. The orchestrator picks it up via the `task` tool.



### Add tools agents use on the workspace

1. Add an `@tool` in `[agents/tools.py](agents/tools.py)`.
2. Attach it to a subagent's `tools` list (see worker for an example).

All agents already get filesystem tools (`read_file`, `write_file`, …), todos,
and — in Docker — `execute` for shell commands against the shared workspace.

### Extend providers or prompts

- Providers: `[agents/providers.py](agents/providers.py)` + `[requirements.txt](requirements.txt)`
- Prompts: `[agents/orchestrator.py](agents/orchestrator.py)`, `[agents/subagents.py](agents/subagents.py)`

Use `#` comments in Python — not docstrings — for in-code notes.

### Security

Docker sandbox = **real shell inside the container**. Do not mount sensitive host
paths or pass secrets you cannot afford to expose. Enabling `AGENT_SANDBOX=1`
locally grants the same shell access on your host.

---



## License

[MIT](LICENSE) © 2026 Made by Aditya Vaish