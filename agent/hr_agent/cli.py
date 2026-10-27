"""Chat with the agent in a terminal.

    python -m hr_agent.cli --employee E001                  # Claude (default)
    HR_AGENT_ENGINE=openai python -m hr_agent.cli           # any OpenAI-compatible model, see portable.py
"""
from __future__ import annotations

import argparse
import asyncio
from datetime import date

from .agent import Trace
from .db import seed
from .engines import engine
from .tools import Session


async def ask_employee(card: str) -> bool:
    print(f"\n--- please confirm ---------------------------\n{card}\n-----------------------------------------------")
    answer = await asyncio.to_thread(input, "Submit this? [y/N] ")   # never block the event loop
    return answer.strip().lower() in {"y", "yes"}


async def chat(session: Session, trace: Trace) -> None:
    """Keep one conversation open across messages, on whichever engine is selected."""
    if engine() == "claude":
        from claude_agent_sdk import ClaudeSDKClient
        from .agent import build_options, run_turn
        async with ClaudeSDKClient(build_options(session, ask_employee, trace)) as client:
            await loop(lambda prompt: run_turn(client, prompt, trace), trace)
    else:
        from .portable import make_client, model_name, new_conversation, run_turn
        client, model, messages = make_client(), model_name(), new_conversation()
        await loop(lambda prompt: run_turn(client, model, session, messages, prompt, ask_employee, trace), trace)


async def loop(turn, trace: Trace) -> None:
    while True:
        prompt = (await asyncio.to_thread(input, "\nyou> ")).strip()
        if not prompt:
            return
        seen = len(trace.tool_calls)
        trace.text, trace.error = "", None
        try:
            await turn(prompt)
        except Exception as exc:
            print(f"  [error] {type(exc).__name__}. Check the selected endpoint, model and credentials privately.")
            continue
        for tool_name, tool_input in trace.tool_calls[seen:]:
            print(f"  [tool] {tool_name} {tool_input}")
        print(f"\nagent> {trace.text}")
        if trace.error:
            print(f"  [stopped] {trace.error}")


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--employee", default="E001", help="who is logged in: E001, E002 or E003")
    parser.add_argument("--today", default="2026-10-19", help="the agent's idea of today (ISO date)")
    args = parser.parse_args()

    session = Session(args.employee, seed(date.fromisoformat(args.today)))
    name = session.db.employees[args.employee].name
    print(f"HR assistant (AI), engine: {engine()}. Logged in as {name}. Empty line to quit.")

    trace = Trace()
    await chat(session, trace)

    db = session.db
    cost = f"estimated cost: ${trace.cost_usd:.4f}" if engine() == "claude" else f"tokens: {trace.tokens}"
    print(f"\nmodel calls: {trace.turns}   {cost}")
    print("requests:", [(r.reference, r.employee_id, str(r.start), str(r.end), r.status) for r in db.requests])
    print("hr cases:", [(c.case_id, c.reason) for c in db.cases])


if __name__ == "__main__":
    asyncio.run(main())
