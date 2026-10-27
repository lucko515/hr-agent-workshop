"""Fast tests for the Claude engine: SDK options, the SDK gate and the audit hook. No model calls."""
import pytest

pytest.importorskip("claude_agent_sdk")
from hr_agent.agent import CARDS, TOOL_TIERS, Trace, build_options, full_name, make_audit_hook, make_gate, submit_card
from hr_agent.tools import build_tools


async def yes(card): return True
async def no(card): return False


def test_every_tool_has_a_tier_and_only_tier_one_is_preapproved(ana):
    opts = build_options(ana, yes, Trace())
    assert {t.name for t in build_tools(ana)} == set(TOOL_TIERS)
    assert full_name("submit_leave_request") not in opts.allowed_tools
    assert set(opts.allowed_tools) == {full_name(t) for t, tier in TOOL_TIERS.items() if tier == 1}
    assert opts.tools == [] and opts.setting_sources == [] and opts.permission_mode == "default"
    assert opts.max_turns and opts.max_budget_usd
    assert {t for t, tier in TOOL_TIERS.items() if tier == 2} == set(CARDS)      # every tier-2 tool has a card


def test_confirmation_card_comes_from_the_tool_call_not_the_model(ana):
    card = submit_card(ana, {"start_date": "2026-11-10", "end_date": "2026-11-12"})
    assert "Ana Kovac (E001)" in card and "2 working day(s)" in card and "12 -> 10" in card


async def test_gate_asks_the_employee_and_denies_everything_else(ana):
    trace = Trace()
    args = {"start_date": "2026-11-03", "end_date": "2026-11-05"}
    allowed = await make_gate(ana, yes, trace)(full_name("submit_leave_request"), args, None)
    refused = await make_gate(ana, no, trace)(full_name("submit_leave_request"), args, None)
    unknown = await make_gate(ana, yes, trace)("Bash", {"command": "ls"}, None)
    assert allowed.behavior == "allow" and allowed.updated_input == args
    assert refused.behavior == "deny" and "said no" in refused.message
    assert unknown.behavior == "deny" and len(trace.confirmations) == 2    # no card for the unknown tool


async def test_audit_hook_logs_every_call_and_blocks_tools_outside_the_server(ana):
    hook = make_audit_hook(ana)
    ok = await hook({"tool_name": full_name("search_policies"), "tool_input": {"query": "leave"}}, "t1", None)
    blocked = await hook({"tool_name": "Read", "tool_input": {"file_path": "/etc/hosts"}}, "t2", None)
    assert ok == {} and blocked["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert [a["allowed"] for a in ana.db.audit] == [True, False]
