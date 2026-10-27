"""Live evals: real model, fake HR system.   pytest -m live tests/evals
   Other engine:  HR_AGENT_ENGINE=openai HR_AGENT_MODEL=... pytest -m live tests/evals   (see hr_agent/portable.py)
   One case:      pytest -m live tests/evals -k L1
   More trials:   EVAL_TRIALS=3 pytest -m live tests/evals
   Read a run:    add -s to print every tool call
"""
import os

import pytest

from hr_agent.engines import engine, get_ask
from hr_agent.db import seed
from hr_agent.tools import Session

from ..conftest import TODAY
from .cases import CASES
from .grade import grade

TRIALS = int(os.environ.get("EVAL_TRIALS", "1"))
RESULTS: list[tuple[str, bool, int, float]] = []


@pytest.mark.live
@pytest.mark.parametrize("case", CASES, ids=[c.id for c in CASES])
async def test_case(case):
    failures: list[str] = []
    for trial in range(TRIALS):
        db = seed(TODAY)                                   # fresh world per trial
        requests_before, cases_before = len(db.requests), len(db.cases)

        async def employee_answers(card: str) -> bool:
            return case.confirm

        trace = await get_ask()(Session(case.employee, db), case.says, employee_answers)
        fails = grade(case, trace, db, requests_before, cases_before)
        RESULTS.append((case.id, not fails, trace.turns, trace.cost_usd))
        usage = f"cost=${trace.cost_usd:.4f}" if engine() == "claude" else f"tokens={trace.tokens}"
        print(f"\n[{case.id} trial {trial + 1}] {'PASS' if not fails else 'FAIL'} turns={trace.turns} {usage}")
        for name, args in trace.tool_calls:
            print(f"    {name} {args}")
        print(f"    answer: {trace.text[:300]}")
        failures += [f"trial {trial + 1}: {f}" for f in fails]
    assert not failures, "\n".join(failures)


def teardown_module():
    if RESULTS:
        passed = sum(ok for _, ok, _, _ in RESULTS)
        cost = sum(c for *_, c in RESULTS)
        turns = sum(t for _, _, t, _ in RESULTS) / len(RESULTS)
        print(f"\n\n=== engine {engine()} | {passed}/{len(RESULTS)} trials passed | avg turns {turns:.1f} | total est. cost ${cost:.2f} ===")
