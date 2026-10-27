"""Small terminal interface to the SAME HR tools used by the application.

Run `python3 hr.py tools`, `python3 hr.py state`, or see --help.
Fictional local prototype: a coding agent with file access can bypass this wrapper.
Real deployment needs a separate service and authenticated identity.
"""
from __future__ import annotations

import argparse
import asyncio
from dataclasses import asdict
from datetime import date
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / 'agent'))
from hr_agent.db import seed, LeaveRequest, HrCase
from hr_agent.tools import Session, build_tools
from hr_agent.agent import TOOL_TIERS, CARDS

STATE = ROOT / 'state.json'


def load():
    db = seed(date(2026, 10, 19))
    pending = None
    if STATE.exists():
        raw = json.loads(STATE.read_text(encoding="utf-8"))
        db.requests = [LeaveRequest(**{**r, 'start': date.fromisoformat(r['start']),
                                      'end': date.fromisoformat(r['end'])}) for r in raw['requests']]
        db.cases = [HrCase(**c) for c in raw['cases']]
        db.audit = raw.get('audit', [])
        pending = raw.get('pending')
    return Session('E001', db), pending


def save(session, pending):
    data = {'employee': 'E001', 'today': str(session.db.today),
            'requests': [asdict(x) for x in session.db.requests],
            'cases': [asdict(x) for x in session.db.cases],
            'audit': session.db.audit, 'pending': pending}
    temp = STATE.with_suffix('.tmp')
    temp.write_text(json.dumps(data, indent=2, default=str))
    temp.replace(STATE)


async def execute(args):
    session, pending = load()
    specs = {t.name: t for t in build_tools(session)}
    if args.command == 'reset':
        session, pending = Session('E001', seed(date(2026, 10, 19))), None
        save(session, pending)
        return {'reset': True, 'employee': 'Ana Kovac', 'today': '2026-10-19'}
    if args.command == 'state':
        return {'requests': [asdict(x) for x in session.db.my_requests('E001')],
                'cases': [asdict(x) for x in session.db.cases if x.employee_id == 'E001'],
                'pending': pending, 'audit': session.db.audit}
    if args.command == 'tools':
        return [{'name': t.name, 'description': t.description, 'inputs': t.input_schema} for t in specs.values()]
    if args.command in ('approve', 'decline'):
        if not pending:
            return {'error': 'No pending action.'}
        if args.command == 'decline':
            session.db.audit.append({'tool': pending['tool'], 'decision': 'declined'})
            save(session, None)
            return {'status': 'declined', 'changed': False}
        # Presenter runs this explicitly after inspecting the card. The actual rule revalidates.
        result = await specs[pending['tool']].handler(pending['args'])
        session.db.audit.append({'tool': pending['tool'], 'decision': 'approved', 'result': result})
        save(session, None)
        return result
    name, inputs = args.tool, json.loads(args.args)
    if not isinstance(inputs, dict):
        raise ValueError('Tool arguments must be a JSON object.')
    if name not in specs or name not in TOOL_TIERS:
        return {'error': f'Unknown or unavailable tool: {name}'}
    if TOOL_TIERS[name] == 2:
        if name not in CARDS:
            return {'error': 'Missing confirmation card; action refused.'}
        if pending and pending != {'tool': name, 'args': inputs}:
            return {'error': 'Resolve the existing pending action before proposing another.'}
        pending = {'tool': name, 'args': inputs}
        save(session, pending)
        return {'status': 'awaiting_human', 'card': CARDS[name](session, inputs),
                'instruction': 'Show this exact card. Ask the human to run python3 hr.py approve or decline. You must not run either command.'}
    result = await specs[name].handler(inputs)
    session.db.audit.append({'tool': name, 'args': inputs, 'result': result})
    save(session, pending)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for command in ('tools', 'state', 'reset', 'approve', 'decline'):
        sub.add_parser(command)
    call = sub.add_parser('call')
    call.add_argument('tool')
    call.add_argument('--args', default='{}')
    try:
        print(json.dumps(asyncio.run(execute(parser.parse_args())), indent=2, default=str))
    except (ValueError, KeyError) as exc:
        print(json.dumps({'error': str(exc)}))
        sys.exit(1)
