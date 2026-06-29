# Supported LLM providers for the sandbox.
#
# LangChain model specs use `provider:model-id`. Friendly aliases (gemini, grok,
# mistral) are normalized in agents/model.py before init_chat_model runs.

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProviderInfo:
    # LangChain provider id passed to init_chat_model.
    provider: str
    # pip install target.
    package: str
    # Env var(s) holding the API key (first match wins).
    env_keys: tuple[str, ...]
    # Example model specs for .env and docs.
    examples: tuple[str, ...]
    # Optional friendly aliases normalized to `provider`.
    aliases: tuple[str, ...] = ()


PROVIDERS: dict[str, ProviderInfo] = {
    "openai": ProviderInfo(
        provider="openai",
        package="langchain-openai",
        env_keys=("OPENAI_API_KEY",),
        examples=(
            "openai:gpt-4.1",
            "openai:gpt-4.1-mini",
            "openai:o3-mini",
        ),
    ),
    "anthropic": ProviderInfo(
        provider="anthropic",
        package="langchain-anthropic",
        env_keys=("ANTHROPIC_API_KEY",),
        examples=(
            "anthropic:claude-opus-4-8",
            "anthropic:claude-sonnet-4-6",
        ),
    ),
    "google_genai": ProviderInfo(
        provider="google_genai",
        package="langchain-google-genai",
        env_keys=("GOOGLE_API_KEY", "GEMINI_API_KEY"),
        examples=(
            "google_genai:gemini-2.5-pro",
            "google_genai:gemini-2.0-flash",
        ),
        aliases=("gemini",),
    ),
    "ollama": ProviderInfo(
        provider="ollama",
        package="langchain-ollama",
        env_keys=(),
        examples=("ollama:llama3.2", "ollama:mistral"),
    ),
    "deepseek": ProviderInfo(
        provider="deepseek",
        package="langchain-deepseek",
        env_keys=("DEEPSEEK_API_KEY",),
        examples=(
            "deepseek:deepseek-chat",
            "deepseek:deepseek-reasoner",
        ),
    ),
    "xai": ProviderInfo(
        provider="xai",
        package="langchain-xai",
        env_keys=("XAI_API_KEY",),
        examples=(
            "xai:grok-3",
            "xai:grok-3-mini",
        ),
        aliases=("grok",),
    ),
    "groq": ProviderInfo(
        provider="groq",
        package="langchain-groq",
        env_keys=("GROQ_API_KEY",),
        examples=(
            "groq:llama-3.3-70b-versatile",
            "groq:mixtral-8x7b-32768",
        ),
    ),
    "mistralai": ProviderInfo(
        provider="mistralai",
        package="langchain-mistralai",
        env_keys=("MISTRAL_API_KEY",),
        examples=(
            "mistralai:mistral-large-latest",
            "mistralai:mistral-small-latest",
        ),
        aliases=("mistral",),
    ),
}

# provider / alias -> canonical provider id
_PROVIDER_LOOKUP: dict[str, str] = {}
for info in PROVIDERS.values():
    _PROVIDER_LOOKUP[info.provider] = info.provider
    for alias in info.aliases:
        _PROVIDER_LOOKUP[alias.lower()] = info.provider


def canonical_provider(name: str) -> str:
    return _PROVIDER_LOOKUP.get(name.lower(), name.lower())


def provider_info(provider: str) -> ProviderInfo | None:
    return PROVIDERS.get(canonical_provider(provider))


def env_keys_for(provider: str) -> tuple[str, ...]:
    info = provider_info(provider)
    return info.env_keys if info else ()


def package_for(provider: str) -> str | None:
    info = provider_info(provider)
    return info.package if info else None


def supported_providers() -> tuple[str, ...]:
    return tuple(PROVIDERS.keys())


def example_specs() -> list[str]:
    specs: list[str] = []
    for info in PROVIDERS.values():
        specs.extend(info.examples)
    return specs
