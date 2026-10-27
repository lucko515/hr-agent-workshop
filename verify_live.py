"""Real model checks. No scripted substitute; failures remain failures."""
from pathlib import Path
import asyncio
from dataclasses import asdict
from datetime import date, datetime, timezone
import json
import os
import sys
import time

ROOT = Path(__file__).resolve().parent
(ROOT / "evidence").mkdir(exist_ok=True)
sys.path.insert(0, str(ROOT / 'agent'))
from hr_agent.db import seed
from hr_agent.tools import Session
from hr_agent.engines import get_ask

CASES = [
    ('policy', 'How many days of annual leave do full-time employees get each year? Cite the policy.', True),
    ('leave_yes', 'Please submit annual leave from 3 to 5 November 2026.', True),
    ('leave_no', 'Please submit annual leave from 3 to 5 November 2026.', False),
    ('escalation', 'I need medical leave tomorrow. Please pass this to HR.', True),
    ('ambiguity', 'I do not know which leave category applies to my situation and I want a person in HR to decide. Please open a case.', True),
    ('onboarding', 'Give me my week-one onboarding checklist, with a separate item for each task.', True),
]


async def main():
    if not os.getenv('HR_AGENT_MODEL'):
        raise SystemExit('Run python3 configure.py first.')
    ask = get_ask()
    results = []
    for name, prompt, decision in CASES:
        db = seed(date(2026, 10, 19))
        async def approve(card):
            print(card, '\nTEST EMPLOYEE DECISION:', decision, flush=True)
            return decision
        start = time.monotonic()
        try:
            trace = await asyncio.wait_for(ask(Session('E001', db), prompt, approve), timeout=150)
            called = [x[0] for x in trace.tool_calls]
            common = not trace.error and bool(trace.text)
            if name == 'policy':
                passed = common and 'search_policies' in called and '25' in trace.text and 'Annual Leave' in trace.text and len(db.requests) == 2 and not db.cases
            elif name == 'leave_yes':
                passed = common and bool(trace.confirmations) and len(db.requests) == 3 and db.requests[-1].working_days == 3 and db.requests[-1].status == 'pending_manager_approval' and 'please confirm' not in trace.text.lower() and 'will review and approve' not in trace.text.lower()
            elif name == 'leave_no':
                passed = common and bool(trace.confirmations) and len(db.requests) == 2
            elif name in ('escalation', 'ambiguity'):
                passed = common and 'escalate_to_hr' in called and len(db.cases) == 1 and len(db.requests) == 2
                if name == 'ambiguity':
                    passed = passed and db.cases[0].reason == 'other'
            else:
                passed = common and 'get_onboarding_checklist' in called and all(w in trace.text.lower() for w in ['laptop', 'security', 'buddy', '5', 'onboarding checklist', '1.8', '2026']) and ('two-factor' in trace.text.lower() or '2fa' in trace.text.lower()) and len(db.requests) == 2 and not db.cases
            result = {'case': name, 'pass': bool(passed), 'seconds': round(time.monotonic()-start, 2),
                      'trace': asdict(trace), 'requests': [asdict(x) for x in db.requests], 'cases': [asdict(x) for x in db.cases]}
        except Exception as exc:
            result = {'case': name, 'pass': False, 'error_type': type(exc).__name__, 'seconds': round(time.monotonic()-start, 2)}
        results.append(result)
        print(name, 'PASS' if result['pass'] else 'FAIL', result['seconds'], 'seconds', flush=True)
    report = {'time_utc': datetime.now(timezone.utc).isoformat(), 'engine': os.getenv('HR_AGENT_ENGINE'),
              'model': os.getenv('HR_AGENT_MODEL'), 'endpoint': os.getenv('OPENAI_BASE_URL', 'provider default'), 'results': results}
    dest = ROOT / 'evidence' / ('live-' + datetime.now().strftime('%Y%m%d-%H%M%S') + '.json')
    dest.write_text(json.dumps(report, indent=2, default=str))
    print('Full evidence:', dest)
    print('PASS here checks selected facts/actions; review answer text for completeness and unsupported claims.')
    return all(x['pass'] for x in results)


if __name__ == '__main__':
    raise SystemExit(0 if asyncio.run(main()) else 1)
