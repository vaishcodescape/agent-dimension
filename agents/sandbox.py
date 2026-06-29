# Docker / local shell sandbox for agent file + command access.
#
# When enabled, agents use deepagents' LocalShellBackend: real files on disk and
# the built-in `execute` tool for arbitrary shell commands inside the container.

from __future__ import annotations

import os
from pathlib import Path

from deepagents.backends import LocalShellBackend

DEFAULT_WORKSPACE = "/workspace"
DEFAULT_EXECUTE_TIMEOUT = 600


def sandbox_enabled() -> bool:
    flag = os.environ.get("AGENT_SANDBOX", "").strip().lower()
    if flag in ("1", "true", "yes", "on"):
        return True
    if flag in ("0", "false", "no", "off"):
        return False
    return Path("/.dockerenv").exists()


def workspace_root() -> str:
    return os.environ.get("AGENT_WORKSPACE", DEFAULT_WORKSPACE)


def execute_timeout() -> int:
    raw = os.environ.get("AGENT_EXECUTE_TIMEOUT", str(DEFAULT_EXECUTE_TIMEOUT))
    return int(raw)


def build_backend() -> LocalShellBackend | None:
    if not sandbox_enabled():
        return None

    root = workspace_root()
    Path(root).mkdir(parents=True, exist_ok=True)

    return LocalShellBackend(
        root_dir=root,
        virtual_mode=False,
        inherit_env=True,
        timeout=execute_timeout(),
    )


def sandbox_prompt_suffix() -> str:
    if not sandbox_enabled():
        return ""
    root = workspace_root()
    return (
        "\n\nSANDBOX: You run in a Linux environment with real shell access. "
        "Subagents can use the `execute` tool to run standard CLI commands "
        "(git, curl, python, pip, make, jq, rg, etc.). "
        f"The workspace directory is `{root}` — use it as the working directory "
        "for execute and for file tool paths."
    )


def list_workspace_files(root: str | None = None, *, max_bytes: int = 100_000) -> dict[str, str]:
    # List workspace files for CLI display when using a disk-backed backend.
    if not sandbox_enabled():
        return {}

    base = Path(root or workspace_root())
    if not base.is_dir():
        return {}

    files: dict[str, str] = {}
    for path in sorted(base.rglob("*")):
        if not path.is_file():
            continue
        rel = str(path.relative_to(base))
        if rel.startswith("."):
            continue
        size = path.stat().st_size
        if size > max_bytes:
            files[rel] = f"<{size} bytes — use read_file or cat via execute>"
            continue
        try:
            files[rel] = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            files[rel] = f"<binary or unreadable, {size} bytes>"
    return files
