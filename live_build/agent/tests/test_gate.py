"""Fast tests for the gate decision both engines share. No model, no SDK."""
from hr_agent.agent import CARDS, TOOL_TIERS, Trace, decide, submit_card
from hr_agent.tools import build_tools


async def yes(card): return True
async def no(card): return False

ARGS = {"start_date": "2026-11-03", "end_date": "2026-11-05"}


def test_every_tool_has_a_tier_and_every_tier_two_tool_has_a_card(ana):
    assert {t.name for t in build_tools(ana)} == set(TOOL_TIERS)
    assert {t for t, tier in TOOL_TIERS.items() if tier == 2} == set(CARDS)


def test_card_comes_from_the_tool_call_not_the_model(ana):
    card = submit_card(ana, {"start_date": "2026-11-10", "end_date": "2026-11-12"})
    assert "Ana Kovac (E001)" in card and "2 working day(s)" in card and "12 -> 10" in card


async def test_tier_one_runs_tier_two_asks_unknown_is_refused(ana):
    trace = Trace()
    assert await decide(ana, "search_policies", {"query": "leave"}, no, trace) is None
    assert await decide(ana, "submit_leave_request", ARGS, yes, trace) is None
    assert "said no" in await decide(ana, "submit_leave_request", ARGS, no, trace)
    assert "not available" in await decide(ana, "delete_all_records", {}, yes, trace)
    assert len(trace.confirmations) == 2                                   # one card per tier-2 call, none for the rest
    assert [a["allowed"] for a in ana.db.audit] == [True, True, True, False]
