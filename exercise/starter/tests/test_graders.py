"""The graders are code too, so they get tests. No model: we hand them made-up traces."""
from datetime import date

from hr_agent.agent import Trace
from hr_agent.db import seed

from .conftest import TODAY
from .evals.cases import CASES, Case
from .evals.grade import grade

BY_ID = {c.id: c for c in CASES}


def test_a_correct_run_passes_and_each_kind_of_mistake_is_caught():
    case = BY_ID["L1-happy-path"]
    db = seed(TODAY)
    db.submit_leave("E001", date(2026, 11, 3), date(2026, 11, 5))
    args = {"start_date": "2026-11-03", "end_date": "2026-11-05"}
    good = Trace(tool_calls=[("check_leave_request", args), ("submit_leave_request", args)])
    assert grade(case, good, db, 2, 0) == []

    skipped_check = Trace(tool_calls=[("submit_leave_request", args)])
    assert "expected a call to check_leave_request" in grade(case, skipped_check, db, 2, 0)

    used_shell = Trace(tool_calls=good.tool_calls + [("Bash", {"command": "ls"})])
    assert any("not one of the HR tools" in f for f in grade(case, used_shell, db, 2, 0))

    assert "expected 1 new leave request(s), found 0" in grade(case, good, seed(TODAY), 2, 0)


def test_over_escalation_and_wrong_reason_are_failures():
    db = seed(TODAY)
    db.open_case("E001", "other", "asked about working from home")
    over = Trace(tool_calls=[("search_policies", {"query": "home"}), ("escalate_to_hr", {})], text="3 days")
    fails = grade(BY_ID["N1-remote-work"], over, db, 2, 0)
    assert "must not call escalate_to_hr" in fails and "expected 0 new HR case(s), found 1" in fails

    sick = Trace(tool_calls=[("escalate_to_hr", {})])
    assert "expected escalation reason sensitive_leave, got other" in grade(BY_ID["E1-sick"], sick, db, 2, 0)


def test_the_set_is_balanced_and_ids_are_unique():
    core = [c for c in CASES if "cancel" not in c.tags]
    assert len({c.id for c in CASES}) == len(CASES)
    assert sum(c.new_cases > 0 for c in core) <= sum("escalate_to_hr" in c.not_called for c in core)
    assert Case("x", "y").new_requests == 0
