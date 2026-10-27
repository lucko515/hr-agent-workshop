"""Run the exact greenfield project being built, never the installed HR reference."""
from pathlib import Path
import os
import subprocess
import sys
from configure import load_config

ROOT = Path(__file__).resolve().parent
PY = ROOT / '.venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
action = sys.argv[1] if len(sys.argv) > 1 else ''
profile = sys.argv[2] if len(sys.argv) > 2 else 'local'
which = sys.argv[3] if len(sys.argv) > 3 else 'live'
if which not in ('live', 'rehearsal'):
    raise SystemExit('Project must be live or rehearsal.')
project = ROOT / 'greenfield' / which
if action not in ('test', 'run', 'verify'):
    raise SystemExit('From delivery: python3 greenfield.py test | run [claude|api|local] | verify [claude|api|local]\nFor prepared fallback append: local rehearsal')
if not PY.exists():
    raise SystemExit('First run python3 install.py')
if action != 'test':
    load_config(profile)
    if os.getenv('HR_AGENT_ENGINE') not in ('openai', 'claude'):
        raise SystemExit('Choose claude, api or local.')
env = os.environ.copy()
env['PYTHONPATH'] = str(project)
args = ['-m','pytest'] if action == 'test' else [str(ROOT/'verify_greenfield.py')] if action == 'verify' else ['main.py']
print('Using greenfield code:', project, flush=True)
raise SystemExit(subprocess.call([str(PY),*args],cwd=project,env=env))
