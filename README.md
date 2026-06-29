# agent-dimension

A multi-agent sandbox where specialized LLM agents coordinate, debate, and run
real work — built on [**deepagents**](https://pypi.org/project/deepagents/) and
[**LangChain**](https://python.langchain.com/) chat models.

Use it to experiment with orchestrator-led task teams, discussion panels, direct
agent-to-agent roundtables, and (in Docker) a Linux environment with shell access.

## What you get

- **Orchestrator + subagents** — a top-level agent delegates to a planner,
  worker, critic, and a three-person discussion panel via deepagents' `task` tool.
- **Multiple LLM providers** — mix OpenAI, Anthropic, Gemini, Groq, xAI (Grok),
  DeepSeek, Mistral, and Ollama across agents in one run.
- **Three front-ends** — interactive chat, one-shot task runner, and a live
  roundtable debate CLI.
- **Docker sandbox** — agents get a persistent `/workspace`, real filesystem I/O,
  and the `execute` tool for shell commands (`git`, `curl`, `python`, `make`, …).

## Architecture

```
                         ┌─────────────────────────────────┐
                         │         orchestrator            │
                         │  (LLM_MODEL — your default)     │
                         └───────────────┬─────────────────┘
                                         │ task tool
           ┌─────────────────────────────┼─────────────────────────────┐
           │                             │                             │
     task team                     discussion panel              built-in tools
  ┌────────┴────────┐          ┌─────────┴─────────┐         ls, read/write,
  │ planner         │          │ optimist          │         edit, glob, grep,
  │ worker (+tools) │          │ skeptic           │         execute*, todos
  │ critic          │          │ pragmatist        │
  └─────────────────┘          └───────────────────┘
           │                             │
           └────────── workspace ────────┘
                 plan.md, discussion.md, …

* execute is available when AGENT_SANDBOX is enabled (Docker by default).
```

**Task flow:** orchestrator → planner (writes `plan.md`) → worker (executes steps)
→ critic (reviews) → orchestrator summarizes.

**Discussion flow:** orchestrator convenes optimist / skeptic / pragmatist; each
appends to `discussion.md` and responds to the others; orchestrator reports the
bottom line.

**Roundtable** (`discuss.py`) skips the orchestrator — personas debate turn-by-turn
in a plain Python loop with live streaming.

## Quick start

### Local (Python 3.14+)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # add API key(s) for the provider(s) you use
```

### Docker (recommended for shell access)

```bash
cp .env.example .env   # add your API key(s)

docker compose build
docker compose run --rm chat          # interactive session
docker compose run --rm run run.py "your task here"
docker compose run --rm discuss discuss.py "Should we ship this week?"
```

The Docker image auto-enables the Linux sandbox (`AGENT_SANDBOX=1`) and mounts a
named volume at `/workspace` so agent output persists across runs.

## Running the agents

### Interactive chat

```bash
python chat.py
# or: docker compose run --rm chat
```

The orchestrator remembers the session. It handles small talk itself, convenes the
task team for real work, or the panel when you ask for debate:

```
you › Should we rewrite the service in Rust? Have the panel debate it.
```

Commands: `/files` · `/reset` · `/help` · `/quit`

### One-shot task

```bash
python run.py "Draft a pitch, have it critiqued, and save the final version to pitch.md"
python run.py   # built-in demo task
```

Streams delegations, tool calls, and workspace files, then exits.

### Roundtable debate

```bash
python discuss.py "Monorepo or polyrepo?"
python discuss.py --rounds 3 --panel optimist,skeptic "Is the deadline realistic?"
```

Each persona reads the transcript and responds by name. No orchestrator, no shared
filesystem — direct model calls only.

## Configuration

Copy [`.env.example`](.env.example) to `.env` and fill in values for the
providers you use. The example file documents **every supported variable** —
defaults, valid values, resolution order, and links to get API keys.

```bash
cp .env.example .env
```

### Quick reference

| Variable | Default | Purpose |
|----------|---------|---------|
| `LLM_MODEL` | `anthropic:claude-opus-4-8` | Orchestrator model (`provider:model-id`) |
| `CLAUDE_MODEL` | — | Legacy fallback; bare id → `anthropic:…` |
| `SUBAGENT_LLM_MODEL` | — | Default model for all subagents |
| `{ROLE}_LLM_MODEL` | — | Per-agent override (`WORKER_`, `SKEPTIC_`, …) |
| `ANTHROPIC_API_KEY` | — | Anthropic / Claude |
| `OPENAI_API_KEY` | — | OpenAI |
| `GOOGLE_API_KEY` / `GEMINI_API_KEY` | — | Gemini (`google_genai`) |
| `DEEPSEEK_API_KEY` | — | DeepSeek |
| `XAI_API_KEY` | — | xAI / Grok |
| `GROQ_API_KEY` | — | Groq |
| `MISTRAL_API_KEY` | — | Mistral |
| `LLM_MAX_TOKENS` | `64000` | Max output tokens per turn |
| `LLM_TEMPERATURE` | — | Temperature (non-Anthropic providers) |
| `CLAUDE_EFFORT` / `LLM_EFFORT` | `max` | Anthropic thinking effort |
| `CLAUDE_THINKING` / `LLM_THINKING` | `true` | Anthropic adaptive thinking |
| `CLAUDE_TASK_BUDGET_TOKENS` | `128000` | Anthropic agentic loop budget |
| `AGENT_SANDBOX` | auto in Docker | Enable shell + disk workspace |
| `AGENT_WORKSPACE` | `/workspace` | Sandbox working directory |
| `AGENT_EXECUTE_TIMEOUT` | `600` | Shell command timeout (seconds) |
| `NO_COLOR` | — | Disable colors in `discuss.py` |

**Model resolution order:** `{ROLE}_LLM_MODEL` → `SUBAGENT_LLM_MODEL` →
`LLM_MODEL` → `CLAUDE_MODEL` → built-in default.

**Supported providers:** `openai`, `anthropic`, `google_genai`, `ollama`,
`deepseek`, `xai`, `groq`, `mistralai` — with aliases `gemini`, `grok`,
`mistral` in model specs.

Install matching packages from [`requirements.txt`](requirements.txt) for each
provider you enable.

### Examples

**Single provider (orchestrator + all agents on Claude):**

```bash
LLM_MODEL=anthropic:claude-opus-4-8
ANTHROPIC_API_KEY=sk-ant-...
```

**Mix providers across agents:**

```bash
LLM_MODEL=anthropic:claude-opus-4-8
WORKER_LLM_MODEL=groq:llama-3.3-70b-versatile
SKEPTIC_LLM_MODEL=xai:grok-3
ANTHROPIC_API_KEY=sk-ant-...
GROQ_API_KEY=gsk_...
XAI_API_KEY=xai-...
```

**Docker sandbox** (shell access — see [`.env.example`](.env.example) sandbox section):

```bash
AGENT_SANDBOX=1
AGENT_WORKSPACE=/workspace
```

Full comments, API key URLs, and Anthropic-only options are in
[`.env.example`](.env.example).

## Project layout

| Path | Role |
|------|------|
| [`agents/orchestrator.py`](agents/orchestrator.py) | Builds the orchestrator via `create_deep_agent` |
| [`agents/subagents.py`](agents/subagents.py) | Task team: planner, worker, critic |
| [`agents/discussants.py`](agents/discussants.py) | Panel personas + shared stances |
| [`agents/model.py`](agents/model.py) | Multi-provider `build_model()` and env resolution |
| [`agents/providers.py`](agents/providers.py) | Provider registry (keys, packages, examples) |
| [`agents/sandbox.py`](agents/sandbox.py) | Docker/local shell backend and workspace helpers |
| [`agents/tools.py`](agents/tools.py) | Example custom `@tool` stubs for the worker |
| [`agents/roundtable.py`](agents/roundtable.py) | Direct turn-by-turn debate engine |
| [`agents/render.py`](agents/render.py) | CLI transcript formatting |
| [`chat.py`](chat.py) | Interactive chat with session memory |
| [`run.py`](run.py) | One-shot task runner |
| [`discuss.py`](discuss.py) | Roundtable debate CLI |
| [`Dockerfile`](Dockerfile) | Python 3.14 image + Linux CLI tools |
| [`docker-compose.yml`](docker-compose.yml) | `chat`, `run`, and `discuss` services |

## For contributors

### Add a subagent

1. Define a `SubAgent` in [`agents/subagents.py`](agents/subagents.py) or
   [`agents/discussants.py`](agents/discussants.py).
2. Append it to `TASK_SUBAGENTS`, `DISCUSSANTS`, or `SUBAGENTS`.
3. Optionally assign a model: `model=build_model_for_role("my_agent")` or a
   spec string like `"openai:gpt-4.1-mini"`.

The orchestrator discovers new agents automatically through the `task` tool.

### Add a custom tool

1. Write an `@tool` function in [`agents/tools.py`](agents/tools.py).
2. Attach it to a subagent's `tools` list in [`agents/subagents.py`](agents/subagents.py).

Every agent already gets deepagents' built-in filesystem and todo tools. In the
Docker sandbox, the `execute` tool runs shell commands in `/workspace`.

### Add or change a provider

Edit [`agents/providers.py`](agents/providers.py):

- Add a `ProviderInfo` entry (provider id, pip package, env keys, examples).
- Add the partner package to [`requirements.txt`](requirements.txt).
- Document the env key in [`.env.example`](.env.example).

Provider specs are normalized in [`agents/model.py`](agents/model.py) (`gemini:`
→ `google_genai:`, etc.).

### Prompts and behavior

- Orchestrator instructions: [`agents/orchestrator.py`](agents/orchestrator.py)
- Subagent roles: [`agents/subagents.py`](agents/subagents.py),
  [`agents/discussants.py`](agents/discussants.py)
- Sandbox context appended at runtime: [`agents/sandbox.py`](agents/sandbox.py)

Keep prompts concise; the orchestrator is the human-facing voice.

### Development tips

```bash
# Validate imports and provider aliases
python -c "from agents import build_orchestrator; print('ok')"

# Rebuild Docker after dependency changes
docker compose build --no-cache

# Inspect workspace after a Docker run
docker compose run --rm run run.py "write hello to /workspace/test.txt"
docker volume inspect agent-dimension_agent-workspace
```

Use hash (`#`) comments in Python modules — docstrings are not used for
documentation in this repo.

### Security note

The Docker sandbox gives agents **real shell access inside the container**. That is
intentional for coding and automation tasks, but treat the container as an
untrusted execution environment:

- Do not mount sensitive host directories into `/workspace`.
- Do not pass production secrets you cannot afford to leak.
- Enabling `AGENT_SANDBOX=1` locally grants the same shell access on your host.

## License

No license file is included yet. Add one before distributing or accepting
external contributions.
