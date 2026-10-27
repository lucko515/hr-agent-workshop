"""Real inference checks for the minimal build. Uses fake HR data, not a fake model."""
import json
import os
from pathlib import Path
import time
from datetime import datetime, timezone
from providers import make_client
import hr

ROOT = Path(__file__).resolve().parent
(ROOT / "evidence").mkdir(exist_ok=True)
cases = [
 ('policy', 'How many annual leave days do employees get? Cite the policy and section.', True),
 ('leave_yes', 'Request annual leave from 2026-11-03 to 2026-11-05.', True),
 ('leave_no', 'Request annual leave from 2026-11-03 to 2026-11-05.', False),
 ('escalation', 'I need time off but do not know which category applies. Please send this to HR.', True),
]
results=[]
client=make_client()
for name,prompt,approval in cases:
    state=hr.make_state(); cards=[]; start=time.monotonic()
    def confirm(card):
        cards.append(str(card)); return approval
    try:
        answer=hr.run_turn(client,state,prompt,confirm)
        if name=='policy':
            passed='25' in answer and 'annual leave' in answer.lower() and not state['requests'] and not state['cases']
        elif name=='leave_yes':
            passed=len(cards)==1 and len(state['requests'])==1 and state['requests'][0]['days']==3 and state['requests'][0]['status']=='pending_manager_approval'
        elif name=='leave_no':
            passed=len(cards)==1 and not state['requests']
        else:
            passed=len(state['cases'])==1 and not state['requests']
        result=dict(case=name,passed=bool(passed),answer=answer,state=state,cards=cards)
    except Exception as exc:
        result=dict(case=name,passed=False,error_type=type(exc).__name__)
    result['seconds']=round(time.monotonic()-start,2);results.append(result)
    print(name, 'PASS' if result['passed'] else 'FAIL', result['seconds'],flush=True)
report=dict(time_utc=datetime.now(timezone.utc).isoformat(),project=str(Path.cwd()),model=os.getenv('HR_AGENT_MODEL'),results=results)
path=ROOT/'evidence'/('greenfield-live-'+datetime.now().strftime('%Y%m%d-%H%M%S')+'.json')
path.write_text(json.dumps(report,indent=2));print('Evidence:',path)
print('These checks cover selected facts and state. Read the answers for unsupported claims.')
raise SystemExit(0 if all(x['passed'] for x in results) else 1)
