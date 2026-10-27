"""Pick the engine the agent runs on. Everything else (tools, rules, tiers, evals) stays the same.

    HR_AGENT_ENGINE=claude   Claude Agent SDK (default). Claude API, or Claude on Bedrock/Vertex/Foundry.
    HR_AGENT_ENGINE=openai   Any OpenAI-compatible endpoint: OpenAI, Azure, Gemini, OpenRouter, Ollama, LM Studio.
"""
from __future__ import annotations

import os

ENGINES = ("claude", "openai")


def engine() -> str:
    name = os.environ.get("HR_AGENT_ENGINE", "claude").lower()
    if name not in ENGINES:
        raise SystemExit(f"HR_AGENT_ENGINE must be one of {', '.join(ENGINES)}, not {name!r}.")
    return name


def get_ask():
    """The one-message `ask(session, prompt, approver) -> Trace` for the selected engine."""
    if engine() == "claude":
        from .agent import ask
    else:
        from .portable import ask
    return ask
