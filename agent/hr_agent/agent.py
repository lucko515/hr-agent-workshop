"""The agent: one model, six tools, one loop. Everything the model must not decide is in code.

Read this file top to bottom in the session. It is the whole agent.
The tier map, the cards and the gate decision at the top are plain Python and are shared with
portable.py, the same agent on any OpenAI-compatible model. Only the runner at the bottom needs
the Claude Agent SDK, and it is imported there, so this file loads without it.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Awaitable, Callable

from .db import working_days_between
from .tools import Session, build_tools

MODEL = os.environ.get("HR_AGENT_MODEL", "claude-sonnet-5-5")
SERVER = "hr"   # dict key in mcp_servers, so Claude sees each tool as mcp__hr__<tool>


def full_name(tool_name: str) -> str:
    return f"mcp__{SERVER}__{tool_name}"

# ---- 1. The autonomy map -------------------------------------------------------------
# Tier 1 runs alone. Tier 2 needs the employee to confirm. Anything not listed is denied.
# Tier 3 (HR decides) and tier 4 (never) are not here because those tools do not exist.
TOOL_TIERS = {
    "search_policies": 1,
    "get_onboarding_checklist": 1,
    "get_my_leave_balance": 1,
    "check_leave_request": 1,
    "escalate_to_hr": 1,
    "submit_leave_request": 2,
}

SYSTEM_PROMPT = """You are the HR assistant for Northwind Ltd. You are an AI, not a person; say so if asked.
You are talking to one logged-in employee and can only see and act on that employee's own data.

What you do:
- Answer HR policy questions using search_policies, and name the document and section you used.
- For onboarding checklists use get_onboarding_checklist with before_day_one, week_one or
  first_month; cite the document and section. Ask which stage if ambiguous. For unsupported stages,
  explain the available stages without guessing tasks. Never claim personal completion status.
- Help with annual leave: get the balance, check the request, then submit it. Submitting asks the
  employee to confirm, and their manager makes the decision. You never approve or decline leave.
- Hand over to a person with escalate_to_hr when the tool description says to.

How you work:
- If dates or intent are unclear, ask one short question instead of guessing.
- If the policies do not answer a question, say so plainly and offer to pass it to HR.
- If a tool reports a problem, explain it in plain words and say what the options are.
- Keep answers short. Today's date and weekday come from get_my_leave_balance."""

# Added after inspecting a real local-model run, not merely its green action checks.
SYSTEM_PROMPT += """

Report outcomes precisely:
- After a successful submission, say it is pending the manager's decision. Never promise
  approval and never ask for confirmation again: the tool already waited for it.
- When the employee asks HR to decide an unspecified leave category, use reason other.
  The case summary must contain only facts supplied by the employee or retrieved from tools.
  Do not claim a policy gap or say policies are unclear unless you actually established that.
- For onboarding answers, cite Onboarding Checklist and its exact section, version and
  effective date. Include every task from that section; do not invent completion status.
"""

# An approver gets the confirmation card and returns True (yes) or False (no).
Approver = Callable[[str], Awaitable[bool]]


@dataclass
class Trace:
    """What one turn did. Evals grade this and the database, never the wording."""
    tool_calls: list[tuple[str, dict[str, Any]]] = field(default_factory=list)   # short names, e.g. "submit_leave_request"
    confirmations: list[str] = field(default_factory=list)
    text: str = ""
    turns: int = 0
    cost_usd: float = 0.0
    tokens: int = 0
    error: str | None = None

    def called(self, tool_name: str) -> bool:
        return any(name == tool_name for name, _ in self.tool_calls)


def submit_card(session: Session, tool_input: dict[str, Any]) -> str:
    emp = session.db.employees[session.employee_id]
    try:
        start = date.fromisoformat(tool_input["start_date"])
        end = date.fromisoformat(tool_input["end_date"])
        days = working_days_between(start, end)
        when = f"{start:%a %d %b %Y} to {end:%a %d %b %Y} ({days} working day(s))"
        after = f"{emp.annual_balance} -> {emp.annual_balance - days}"
    except (KeyError, ValueError, TypeError):
        when, after = f"unreadable dates: {tool_input}", "unknown"
    return (f"Submit ANNUAL LEAVE for {emp.name} ({emp.id})\n"
            f"  Dates:   {when}\n  Balance: {after} days\n  Goes to: your line manager for approval")


# One card builder per tier-2 tool. A card is built from the actual pending tool call and the
# database, never from the model's summary. A tier-2 tool with no card here is denied.
CARDS: dict[str, Callable[[Session, dict[str, Any]], str]] = {
    "submit_leave_request": submit_card,
}


async def decide(session: Session, tool_name: str, tool_input: dict[str, Any], approver: Approver, trace: Trace) -> str | None:
    """2. The approval gate, without any SDK. Returns None to allow, or the reason it was refused.

    Every tool call is logged first. Tier 1 runs. Tier 2 shows a card and waits for a yes.
    Anything not in the tier map is refused. Both runners call this before every tool call.
    """
    tier = TOOL_TIERS.get(tool_name)
    session.db.audit.append({"employee": session.employee_id, "tool": tool_name, "input": tool_input, "allowed": tier in (1, 2)})
    if tier == 1:
        return None
    if tier != 2 or tool_name not in CARDS:
        return f"{tool_name} is not available to this assistant."
    card = CARDS[tool_name](session, tool_input)
    trace.confirmations.append(card)
    if await approver(card):
        return None
    return "The employee said no. Nothing was changed. Ask what they want to do instead."


# ---- The runner for Claude (Claude Agent SDK) ---------------------------------------------
# For OpenAI, Azure, Gemini, OpenRouter or a local model, see portable.py instead.

def build_server(session: Session):
    """Wrap the plain tools from tools.py as an in-process MCP server for the Claude Agent SDK."""
    from claude_agent_sdk import create_sdk_mcp_server, tool
    sdk_tools = [tool(t.name, t.description, t.input_schema)(t.handler) for t in build_tools(session)]
    return create_sdk_mcp_server(name=SERVER, version="1.0.0", tools=sdk_tools)


def make_gate(session: Session, approver: Approver, trace: Trace):
    """The Claude SDK calls this only for tool calls nothing earlier approved (tier 2)."""
    from claude_agent_sdk import PermissionResultAllow, PermissionResultDeny

    async def gate(tool_name: str, tool_input: dict[str, Any], context: Any):
        refusal = await decide(session, tool_name.removeprefix(f"mcp__{SERVER}__"), tool_input, approver, trace)
        if refusal is None:
            return PermissionResultAllow(updated_input=tool_input)
        return PermissionResultDeny(message=refusal)
    return gate


def make_audit_hook(session: Session):
    """3. A deterministic check that runs before every tool call, in every permission mode.
    Blocks anything outside the HR tools. Tier 1 calls are logged here; tier 2 is logged by decide()."""
    async def audit(input_data: dict[str, Any], tool_use_id: str | None, context: Any) -> dict[str, Any]:
        name = input_data.get("tool_name", "")
        short = name.removeprefix(f"mcp__{SERVER}__")
        allowed = name.startswith(f"mcp__{SERVER}__") and short in TOOL_TIERS
        if not allowed or TOOL_TIERS.get(short) == 1:
            # Log identifiers and parameters, not conversation text.
            session.db.audit.append({"employee": session.employee_id, "tool": short, "input": input_data.get("tool_input"), "allowed": allowed})
        if allowed:
            return {}
        return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                       "permissionDecisionReason": f"{name} is not part of the HR assistant."}}
    return audit


def build_options(session: Session, approver: Approver, trace: Trace):
    """4. Every default that differs between machines is pinned here on purpose."""
    import warnings
    from claude_agent_sdk import CanUseToolShadowedWarning, ClaudeAgentOptions, HookMatcher
    # The SDK warns that pre-approved tools skip the gate. That is the design: tier 1 runs alone,
    # tier 2 goes to the gate. The test suite checks the two lists match.
    warnings.filterwarnings("ignore", category=CanUseToolShadowedWarning)
    return ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        model=MODEL,
        tools=[],                                    # no built-in file, shell or web tools at all
        mcp_servers={SERVER: build_server(session)},
        allowed_tools=[full_name(t) for t, tier in TOOL_TIERS.items() if tier == 1],  # pre-approved
        permission_mode="default",                   # so tier 2 falls through to the gate
        can_use_tool=make_gate(session, approver, trace),
        hooks={"PreToolUse": [HookMatcher(hooks=[make_audit_hook(session)])]},
        setting_sources=[],                          # ignore CLAUDE.md and settings on this machine
        strict_mcp_config=True,                      # ignore MCP servers configured on this machine
        verbatim_prompts=True,                       # employee text is data: no @file or /command expansion
        env={"ENABLE_TOOL_SEARCH": "false"},
        max_turns=12,
        max_budget_usd=0.50,
    )


async def run_turn(client, prompt: str, trace: Trace) -> Trace:
    from claude_agent_sdk import AssistantMessage, ResultMessage, TextBlock, ToolUseBlock
    await client.query(prompt)
    async for message in client.receive_response():
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, ToolUseBlock):
                    trace.tool_calls.append((block.name.removeprefix(f"mcp__{SERVER}__"), dict(block.input)))
                elif isinstance(block, TextBlock):
                    trace.text = block.text          # keep the last text block as the answer
        elif isinstance(message, ResultMessage):
            trace.turns = message.num_turns
            trace.cost_usd = message.total_cost_usd or 0.0
            if message.is_error:
                trace.error = f"{message.subtype}: {message.result}"
    return trace


async def ask(session: Session, prompt: str, approver: Approver) -> Trace:
    """One isolated conversation with one message. Used by evals and by the smoke test."""
    from claude_agent_sdk import ClaudeSDKClient
    trace = Trace()
    async with ClaudeSDKClient(build_options(session, approver, trace)) as client:
        await run_turn(client, prompt, trace)
    return trace
