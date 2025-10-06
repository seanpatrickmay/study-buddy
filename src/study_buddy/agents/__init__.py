"""CrewAI agent helpers and shared configuration."""

from __future__ import annotations

from study_buddy.config import (
    ANTHROPIC_MODEL_ALIASES,
    DEFAULT_ANTHROPIC_MODEL,
    settings,
)


def default_agent_llm(model: str | None = None) -> str:
    """Return the provider-qualified model name expected by CrewAI/LiteLLM."""
    raw = (model or settings.llm_model or DEFAULT_ANTHROPIC_MODEL).strip()

    if not raw:
        raw = DEFAULT_ANTHROPIC_MODEL

    # Normalise by stripping provider prefixes before alias lookup
    candidate = raw.split("/", 1)[1] if raw.lower().startswith("anthropic/") else raw
    alias = (
        ANTHROPIC_MODEL_ALIASES.get(candidate)
        or ANTHROPIC_MODEL_ALIASES.get(candidate.lower())
        or ANTHROPIC_MODEL_ALIASES.get(raw)
        or ANTHROPIC_MODEL_ALIASES.get(raw.lower())
    )
    chosen = alias or candidate or DEFAULT_ANTHROPIC_MODEL

    if chosen.lower().startswith("anthropic/"):
        return chosen

    if "/" in chosen:
        return chosen

    if chosen.lower().startswith("claude"):
        return f"anthropic/{chosen}"

    return chosen
