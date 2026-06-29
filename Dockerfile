FROM python:3.14-slim-bookworm

# Common Linux CLI tools agents can invoke via deepagents' `execute` tool.
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    build-essential \
    ca-certificates \
    curl \
    file \
    findutils \
    git \
    grep \
    jq \
    less \
    make \
    openssh-client \
    procps \
    ripgrep \
    rsync \
    sed \
    tar \
    unzip \
    wget \
    zip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    AGENT_SANDBOX=1 \
    AGENT_WORKSPACE=/workspace \
    AGENT_EXECUTE_TIMEOUT=600 \
    LLM_MODEL=anthropic:claude-opus-4-8 \
    CLAUDE_EFFORT=max \
    CLAUDE_MAX_TOKENS=64000 \
    CLAUDE_TASK_BUDGET_TOKENS=128000 \
    CLAUDE_THINKING=true

RUN mkdir -p /workspace

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agents/ agents/
COPY chat.py discuss.py run.py ./

VOLUME ["/workspace"]

ENTRYPOINT ["python"]
CMD ["chat.py"]
