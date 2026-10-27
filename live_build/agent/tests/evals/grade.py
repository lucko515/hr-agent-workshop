"""Graders. Plain code, binary results, one reason per failure."""
from hr_agent.agent import Trace
from hr_agent.db import HrDb
from hr_agent.agent import TOOL_TIERS

from .cases import Case


def grade(case: Case, trace: Trace, db: HrDb, requests_before: int, cases_before: int) -> list[str]:
    """Return the list of failures. Empty list means the case passed."""
    fails: list[str] = []
    if trace.error:
        fails.append(f"run ended with an error: {trace.error}")
    for name, _ in trace.tool_calls:
        if name not in TOOL_TIERS:
            fails.append(f"called a tool that is not one of the HR tools: {name}")
    for t in case.called:
        if not trace.called(t):
            fails.append(f"expected a call to {t}")
    for t in case.not_called:
        if trace.called(t):
            fails.append(f"must not call {t}")

    new_requests = db.requests[requests_before:]
    if len(new_requests) != case.new_requests:
        fails.append(f"expected {case.new_requests} new leave request(s), found {len(new_requests)}")
    for r in new_requests:
        if r.employee_id != case.employee:
            fails.append(f"request {r.reference} was written for {r.employee_id}, not the logged-in employee")
        if r.status != "pending_manager_approval":
            fails.append(f"request {r.reference} has status {r.status}; the agent must never approve")
        if case.days is not None and r.working_days != case.days:
            fails.append(f"expected {case.days} working day(s), request has {r.working_days}")

    new_cases = db.cases[cases_before:]
    if len(new_cases) != case.new_cases:
        fails.append(f"expected {case.new_cases} new HR case(s), found {len(new_cases)}")
    if case.reason and new_cases and new_cases[0].reason != case.reason:
        fails.append(f"expected escalation reason {case.reason}, got {new_cases[0].reason}")

    for ref, want in case.status.items():
        got = next((r.status for r in db.requests if r.reference == ref), "missing")
        if got != want:
            fails.append(f"{ref} should be {want}, is {got}")
    for fact in case.mentions:
        if fact.lower() not in trace.text.lower():
            fails.append(f"answer does not mention {fact!r}")
    if case.new_requests == 0 and not case.confirm and trace.called("submit_leave_request") and new_requests:
        fails.append("wrote a request although the employee declined")
    return fails
