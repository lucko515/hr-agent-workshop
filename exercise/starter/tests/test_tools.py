"""Fast tests. No model, no network. They call the tool handlers directly."""
from datetime import date

from hr_agent import policy_search
from hr_agent.tools import Session

from .conftest import text_of, tools_for


async def test_balance_is_always_the_logged_in_employee(db):
    marko = tools_for(Session("E002", db))
    out = text_of(await marko["get_my_leave_balance"]({"employee_id": "E001"}))   # extra arg is ignored
    assert "Marko Ilic: 2 working days" in out and "Ana" not in out


async def test_check_counts_working_days_and_skips_the_public_holiday(ana):
    out = await tools_for(ana)["check_leave_request"]({"start_date": "2026-11-10", "end_date": "2026-11-12"})
    assert not out["is_error"] and "2 working day(s)" in text_of(out)       # 11 Nov is a holiday


async def test_check_explains_each_failed_rule(db, ana):
    t = tools_for(ana)
    assert "before start date" in text_of(await t["check_leave_request"]({"start_date": "2026-11-05", "end_date": "2026-11-03"}))
    assert "not in the future" in text_of(await t["check_leave_request"]({"start_date": "2026-10-01", "end_date": "2026-10-02"}))
    assert "Notice too short" in text_of(await t["check_leave_request"]({"start_date": "2026-10-20", "end_date": "2026-10-20"}))
    assert "Overlaps existing request LR-1001" in text_of(await t["check_leave_request"]({"start_date": "2026-11-23", "end_date": "2026-11-23"}))
    vague = await t["check_leave_request"]({"start_date": "mid November", "end_date": "soon"})
    assert vague["is_error"] and "Do not guess" in text_of(vague)

    marko = tools_for(Session("E002", db))
    assert "Not enough balance" in text_of(await marko["check_leave_request"]({"start_date": "2026-11-09", "end_date": "2026-11-13"}))
    assert "year-end closure" in text_of(await marko["check_leave_request"]({"start_date": "2026-12-22", "end_date": "2026-12-22"}))


async def test_submit_writes_once_revalidates_and_never_approves(db, ana):
    t = tools_for(ana)
    first = text_of(await t["submit_leave_request"]({"start_date": "2026-11-03", "end_date": "2026-11-05"}))
    again = text_of(await t["submit_leave_request"]({"start_date": "2026-11-03", "end_date": "2026-11-05"}))
    mine = [r for r in db.requests if r.start == date(2026, 11, 3)]
    assert "Submitted: LR-1003" in first and "Already submitted" in again and len(mine) == 1
    assert mine[0].employee_id == "E001" and mine[0].status == "pending_manager_approval"

    bad = await t["submit_leave_request"]({"start_date": "2026-10-20", "end_date": "2026-10-20"})   # skipped the check tool
    assert bad["is_error"] and "Not submitted" in text_of(bad) and len(db.requests) == 3


async def test_escalation_opens_a_case_and_rejects_unknown_reasons(db, ana):
    t = tools_for(ana)
    ok = text_of(await t["escalate_to_hr"]({"reason": "sensitive_leave", "summary": "Employee reports being unwell tomorrow."}))
    bad = await t["escalate_to_hr"]({"reason": "because", "summary": "x"})
    assert "Case HR-5001" in ok and bad["is_error"] and len(db.cases) == 1 and db.cases[0].employee_id == "E001"


def test_search_cites_documents_and_surfaces_the_conflict():
    top = policy_search.search("annual leave entitlement days")[0]
    assert top.title == "Annual Leave Policy" and "25 working days" in top.text

    titles = {h.title for h in policy_search.search("meal limit business travel")}
    assert {"Expenses Policy", "Travel Booking FAQ"} <= titles                # 45 EUR vs 60 EUR: both must show up
    assert policy_search.search("pet insurance") == []
