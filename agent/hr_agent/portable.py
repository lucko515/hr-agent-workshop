"""HR agent runner for endpoints that support Chat Completions with function tools.

Configure OPENAI_BASE_URL, OPENAI_API_KEY and HR_AGENT_MODEL through the delivery
configuration helper. HR_AGENT_REASONING_EFFORT is optional and model-dependent.
The tools, rules and confirmation gate are shared with the Claude runner.
Compatibility must be tested for the exact endpoint and model. A chat website,
Responses-only model or nonstandard gateway is not automatically supported.
"""
from __future__ import annotations

import json
import os
from typing import Any

from .agent import SYSTEM_PROMPT, Approver, Trace, decide
from .tools import Session, build_tools

MAX_TURNS = 12   # model calls per message, the same limit the Claude version uses


def model_name() -> str:
    model = os.environ.get("HR_AGENT_MODEL", "")
    if not model or model.startswith("claude-"):
        raise SystemExit("Set HR_AGENT_MODEL to a model your endpoint serves, e.g. qwen3:4b for Ollama.")
    return model


def make_client():
    """Reads OPENAI_API_KEY and OPENAI_BASE_URL from the environment, like any OpenAI client."""
    from openai import AsyncOpenAI
    return AsyncOpenAI(timeout=45, max_retries=0)


def openai_tools(session: Session) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """The same tools, described in the shape the Chat Completions API expects."""
    specs = {t.name: t for t in build_tools(session)}
    schema = [{"type": "function", "function": {"name": t.name, "description": t.description, "parameters": t.input_schema}}
              for t in specs.values()]
    return schema, specs


async def run_turn(client, model: str, session: Session, messages: list[dict[str, Any]],
                   prompt: str, approver: Approver, trace: Trace) -> Trace:
    """One employee message. `messages` holds the whole conversation and grows every call."""
    tools, specs = openai_tools(session)
    extra = {"reasoning_effort": effort} if (effort := os.environ.get("HR_AGENT_REASONING_EFFORT")) else {}
    messages.append({"role": "user", "content": prompt})

    for _ in range(MAX_TURNS):
        # 1. Send everything: system prompt, tool descriptions, the conversation so far.
        response = await client.chat.completions.create(model=model, messages=messages, tools=tools, **extra)
        trace.turns += 1
        if response.usage:
            trace.tokens += response.usage.total_tokens or 0
        message = response.choices[0].message

        # 2. The model answers with text (done) or with tool requests.
        calls = message.tool_calls or []
        messages.append({"role": "assistant", "content": message.content or "",
                         **({"tool_calls": [{"id": c.id, "type": "function",
                                             "function": {"name": c.function.name, "arguments": c.function.arguments}}
                                            for c in calls]} if calls else {})})
        if not calls:
            trace.text = message.content or ""
            return trace

        # 3. Your code decides whether each tool runs, runs it, and adds the result.
        for call in calls:
            name = call.function.name
            try:
                args = json.loads(call.function.arguments or "{}")
            except json.JSONDecodeError:
                args = None
            trace.tool_calls.append((name, args if isinstance(args, dict) else {}))

            if not isinstance(args, dict):
                result = "The arguments were not valid JSON. Call the tool again with valid JSON."
            elif (refusal := await decide(session, name, args, approver, trace)) is not None:
                result = refusal
            elif name not in specs:
                result = f"{name} is not available to this assistant."
            else:
                result = (await specs[name].handler(args))["content"][0]["text"]
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result})
        # 4. Back to the top: send everything again.

    trace.error = f"stopped after {MAX_TURNS} model calls without a final answer"
    return trace


def new_conversation() -> list[dict[str, Any]]:
    return [{"role": "system", "content": SYSTEM_PROMPT}]


async def ask(session: Session, prompt: str, approver: Approver) -> Trace:
    """One isolated conversation with one message. Used by evals and the preflight check."""
    trace = Trace()
    try:
        await run_turn(make_client(), model_name(), session, new_conversation(), prompt, approver, trace)
    except SystemExit:
        raise
    except Exception as exc:                       # network, auth, unknown model: report, do not crash the eval run
        trace.error = f"{type(exc).__name__}: {str(exc)[:300]}"
    return trace
