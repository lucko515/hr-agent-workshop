"""In-memory HR system. This is the agent's whole world, and the thing evals grade.

Nothing here talks to a model. Every rule that can be a rule lives here, in code.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

PUBLIC_HOLIDAYS = {
    date(2026, 11, 11), date(2026, 12, 25),
    date(2027, 1, 1), date(2027, 1, 7), date(2027, 2, 15), date(2027, 2, 16),
}
MAX_CONSECUTIVE_DAYS = 15
SHORT_NOTICE_DAYS = 2      # for requests of 1 to 5 working days
LONG_NOTICE_DAYS = 10      # for requests of more than 5 working days


@dataclass
class Employee:
    id: str
    name: str
    department: str
    manager_id: str
    annual_balance: int


@dataclass
class LeaveRequest:
    reference: str
    employee_id: str
    start: date
    end: date
    working_days: int
    status: str = "pending_manager_approval"


@dataclass
class HrCase:
    case_id: str
    employee_id: str
    reason: str
    summary: str


@dataclass
class Check:
    """Result of validating a leave request. `ok` is the only thing code should branch on."""
    ok: bool
    working_days: int = 0
    balance_after: int = 0
    problems: list[str] = field(default_factory=list)
    needs_hr: bool = False     # True when a human in HR has to decide, not the employee


def is_working_day(d: date) -> bool:
    return d.weekday() < 5 and d not in PUBLIC_HOLIDAYS


def working_days_between(start: date, end: date) -> int:
    return sum(is_working_day(start + timedelta(days=i)) for i in range((end - start).days + 1))


@dataclass
class HrDb:
    today: date
    employees: dict[str, Employee]
    requests: list[LeaveRequest] = field(default_factory=list)
    cases: list[HrCase] = field(default_factory=list)
    audit: list[dict] = field(default_factory=list)

    # ---- reads -----------------------------------------------------------
    def my_requests(self, employee_id: str) -> list[LeaveRequest]:
        return [r for r in self.requests if r.employee_id == employee_id]

    # ---- the rules -------------------------------------------------------
    def check_leave(self, employee_id: str, start: date, end: date) -> Check:
        emp = self.employees[employee_id]
        problems: list[str] = []
        needs_hr = False

        if end < start:
            return Check(False, problems=[f"End date {end} is before start date {start}. Swap them or ask the employee."])
        if start <= self.today:
            return Check(False, problems=[f"Start date {start} is not in the future. Today is {self.today}."])

        days = working_days_between(start, end)
        if days == 0:
            return Check(False, problems=[f"{start} to {end} contains no working days (weekend or public holiday)."])

        notice = working_days_between(self.today + timedelta(days=1), start - timedelta(days=1))
        required = SHORT_NOTICE_DAYS if days <= 5 else LONG_NOTICE_DAYS
        if notice < required:
            problems.append(
                f"Notice too short: {days} working day(s) of leave need {required} working days of notice, "
                f"this gives {notice}. An exception needs HR."
            )
            needs_hr = True
        if days > MAX_CONSECUTIVE_DAYS:
            problems.append(f"{days} working days exceeds the {MAX_CONSECUTIVE_DAYS}-day maximum. Longer absences are handled by HR.")
            needs_hr = True
        if days > emp.annual_balance:
            problems.append(
                f"Not enough balance: request is {days} working day(s), balance is {emp.annual_balance}. "
                "The employee can shorten the request; a negative balance needs HR."
            )
        if emp.department == "Operations" and start <= date(start.year, 12, 31) and end >= date(start.year, 12, 21):
            problems.append("Operations cannot take annual leave from 21 to 31 December (year-end closure). An exception needs HR.")
            needs_hr = True
        for r in self.my_requests(employee_id):
            if r.status != "cancelled" and r.start <= end and start <= r.end:
                problems.append(f"Overlaps existing request {r.reference} ({r.start} to {r.end}).")

        return Check(not problems, days, emp.annual_balance - days, problems, needs_hr)

    # ---- writes ----------------------------------------------------------
    def submit_leave(self, employee_id: str, start: date, end: date) -> tuple[LeaveRequest, bool]:
        """Write one pending request. Idempotent: the same dates return the same row.

        Re-validates, because a write tool never trusts that a check tool was called first.
        Returns (request, created).
        """
        for r in self.my_requests(employee_id):
            if r.start == start and r.end == end and r.status != "cancelled":
                return r, False
        check = self.check_leave(employee_id, start, end)
        if not check.ok:
            raise ValueError(" ".join(check.problems))
        ref = f"LR-{1001 + len(self.requests)}"
        req = LeaveRequest(ref, employee_id, start, end, check.working_days)
        self.requests.append(req)
        return req, True

    def open_case(self, employee_id: str, reason: str, summary: str) -> HrCase:
        case = HrCase(f"HR-{5001 + len(self.cases)}", employee_id, reason, summary)
        self.cases.append(case)
        return case


def seed(today: date | None = None) -> HrDb:
    """Fresh database. Tests and evals call this once per case so trials never share state."""
    db = HrDb(
        today=today or date.today(),
        employees={
            "E001": Employee("E001", "Ana Kovac", "Engineering", "E010", annual_balance=12),
            "E002": Employee("E002", "Marko Ilic", "Operations", "E010", annual_balance=2),
            "E003": Employee("E003", "Lena Novak", "Finance", "E011", annual_balance=25),
        },
    )
    # One existing request each, so "my requests" and overlap checks have something to find.
    db.requests.append(LeaveRequest("LR-1001", "E001", date(2026, 11, 23), date(2026, 11, 24), 2))
    db.requests.append(LeaveRequest("LR-1002", "E002", date(2026, 11, 30), date(2026, 11, 30), 1))
    return db
