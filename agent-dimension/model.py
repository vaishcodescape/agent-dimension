# Multi-provider LLM construction for the sandbox.
#
# Agents run on any supported provider via `provider:model-id` specs:
#   openai, anthropic, google_genai (alias: gemini), ollama, deepseek,
#   xai (alias: grok), groq, mistralai (alias: mistral)

from __future__ import annotations

import os

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel

from deepagents.profiles.provider.provider_profiles import apply_provider_profile

from agents.providers import (
    canonical_provider,
    env_keys_for,
    package_for,
    supported_providers,
)

DEFAULT_ANTHROPIC_MODEL = "claude-opus-4-8"
DEFAULT_MODEL_SPEC = f"anthropic:{DEFAULT_ANTHROPIC_MODEL}"
DEFAULT_MAX_TOKENS = 64_000
DEFAULT_EFFORT = "max"
DEFAULT_TASK_BUDGET_TOKENS = 128_000

# Back-compat alias used by older imports.
DEFAULT_MODEL = DEFAULT_MODEL_SPEC


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    return int(raw)


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def normalize_model_spec(spec: str) -> str:
    # Bare model ids (legacy CLAUDE_MODEL) map to Anthropic.
    # Friendly aliases: gemini:* -> google_genai:*, grok:* -> xai:*.
    spec = spec.strip()
    if not spec:
        return DEFAULT_MODEL_SPEC
    if ":" not in spec:
        return f"anthropic:{spec}"

    provider, _, model_id = spec.partition(":")
    provider = canonical_provider(provider)
    if provider not in supported_providers():
        names = ", ".join(sorted(supported_providers()))
        raise ValueError(
            f"Unsupported provider {provider!r} in {spec!r}. "
            f"Supported: {names} (gemini and grok are aliases)."
        )
    return f"{provider}:{model_id}"


def parse_model_spec(spec: str) -> tuple[str, str, str]:
    # Returns (provider, model_id, full_spec).
    full = normalize_model_spec(spec)
    provider, _, model_id = full.partition(":")
    return provider.lower(), model_id, full


def default_model_spec() -> str:
    if spec := os.environ.get("LLM_MODEL"):
        return normalize_model_spec(spec)
    if legacy := os.environ.get("CLAUDE_MODEL"):
        return normalize_model_spec(legacy)
    return DEFAULT_MODEL_SPEC


def model_spec_for(role: str | None = None) -> str:
    # Per-agent override: WORKER_LLM_MODEL, SKEPTIC_LLM_MODEL, etc.
    if role:
        env_key = f"{role.upper()}_LLM_MODEL"
        if override := os.environ.get(env_key):
            return normalize_model_spec(override)
    if sub := os.environ.get("SUBAGENT_LLM_MODEL"):
        return normalize_model_spec(sub)
    return default_model_spec()


def missing_credentials_message(model: str | BaseChatModel | None = None) -> str | None:
    if isinstance(model, BaseChatModel):
        return None

    spec = normalize_model_spec(model) if model else default_model_spec()
    provider, _, _ = parse_model_spec(spec)
    keys = env_keys_for(provider)
    if not keys:
        return None
    if any(os.environ.get(key) for key in keys):
        return None
    key_list = " or ".join(keys)
    return (
        f"{key_list} is not set (needed for {spec}).\n"
        "Copy .env.example to .env and add your key:\n"
        "    cp .env.example .env"
    )


def missing_package_message(model: str) -> str | None:
    provider, _, _ = parse_model_spec(model)
    pkg = package_for(provider)
    if not pkg:
        return None

    module_map = {
        "langchain-anthropic": "langchain_anthropic",
        "langchain-openai": "langchain_openai",
        "langchain-google-genai": "langchain_google_genai",
        "langchain-groq": "langchain_groq",
        "langchain-xai": "langchain_xai",
        "langchain-deepseek": "langchain_deepseek",
        "langchain-mistralai": "langchain_mistralai",
        "langchain-ollama": "langchain_ollama",
    }
    module = module_map.get(pkg, pkg.replace("-", "_"))
    try:
        __import__(module)
    except ImportError:
        return (
            f"Provider package not installed for {model}.\n"
            f"    pip install {pkg}"
        )
    return None


def collect_credentials_errors(*specs: str | None) -> str | None:
    seen: set[str] = set()
    for spec in specs:
        resolved = normalize_model_spec(spec) if spec else default_model_spec()
        if resolved in seen:
            continue
        seen.add(resolved)
        if err := missing_credentials_message(resolved):
            return err
        if err := missing_package_message(resolved):
            return err
    return None


def _anthropic_kwargs(
    *,
    max_tokens: int,
    thinking: bool,
    effort: str | None,
    task_budget_tokens: int,
) -> dict:
    kwargs: dict = {"max_tokens": max_tokens}
    if thinking:
        kwargs["thinking"] = {"type": "adaptive"}
    if effort:
        kwargs["effort"] = effort
    if task_budget_tokens > 0:
        kwargs["output_config"] = {
            "task_budget": {"type": "tokens", "total": task_budget_tokens},
        }
    return kwargs


def build_model(
    model: str | BaseChatModel | None = None,
    max_tokens: int | None = None,
    thinking: bool | None = None,
    effort: str | None = None,
    task_budget_tokens: int | None = None,
    temperature: float | None = None,
) -> BaseChatModel:
    if isinstance(model, BaseChatModel):
        return model

    spec = normalize_model_spec(model) if model else default_model_spec()
    provider, _, full_spec = parse_model_spec(spec)

    if err := missing_package_message(full_spec):
        raise ImportError(err)

    token_limit = (
        max_tokens
        if max_tokens is not None
        else _env_int("LLM_MAX_TOKENS", _env_int("CLAUDE_MAX_TOKENS", DEFAULT_MAX_TOKENS))
    )

    if provider == "anthropic":
        use_thinking = (
            thinking
            if thinking is not None
            else _env_bool("CLAUDE_THINKING", _env_bool("LLM_THINKING", True))
        )
        effort_level = (
            effort
            or os.environ.get("CLAUDE_EFFORT")
            or os.environ.get("LLM_EFFORT")
            or DEFAULT_EFFORT
        )
        if task_budget_tokens is not None:
            budget = task_budget_tokens
        elif os.environ.get("CLAUDE_TASK_BUDGET_TOKENS") is not None:
            budget = _env_int("CLAUDE_TASK_BUDGET_TOKENS", DEFAULT_TASK_BUDGET_TOKENS)
        elif os.environ.get("LLM_TASK_BUDGET_TOKENS") is not None:
            budget = _env_int("LLM_TASK_BUDGET_TOKENS", DEFAULT_TASK_BUDGET_TOKENS)
        else:
            budget = DEFAULT_TASK_BUDGET_TOKENS

        extra = _anthropic_kwargs(
            max_tokens=token_limit,
            thinking=use_thinking,
            effort=effort_level,
            task_budget_tokens=budget,
        )
        if temperature is not None:
            extra["temperature"] = temperature
        return init_chat_model(full_spec, **extra)

    init_kwargs = dict(apply_provider_profile(full_spec))
    init_kwargs["max_tokens"] = token_limit
    if temperature is not None:
        init_kwargs["temperature"] = temperature
    elif temp := os.environ.get("LLM_TEMPERATURE"):
        init_kwargs["temperature"] = float(temp)

    return init_chat_model(full_spec, **init_kwargs)


def build_model_for_role(role: str, **kwargs) -> BaseChatModel:
    return build_model(model=model_spec_for(role), **kwargs)
