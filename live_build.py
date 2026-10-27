"""Prepare, build, test and run the SAME live workshop copy."""
from pathlib import Path
import os
import shutil
import subprocess
import sys
from configure import load_config

ROOT = Path(__file__).resolve().parent
WORK = ROOT / 'live_build'
APP = WORK / 'agent'
PY = ROOT / '.venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
action = sys.argv[1] if len(sys.argv) > 1 else ''

if action == 'prepare':
    if WORK.exists():
        raise SystemExit('live_build already exists. Preserved it. For a fresh rehearsal, rename that folder first, then prepare again.')
    shutil.copytree(ROOT / 'exercise/starter', APP,
                    ignore=shutil.ignore_patterns('.venv', '__pycache__', '.pytest_cache', '*.egg-info'))
    prompt = (ROOT / 'prompts/brownfield/B1_RED.txt').read_text(encoding="utf-8")
    prompt += '\nThis is the LIVE workshop copy. Work only in this folder. Run tests with ../../.venv/bin/python -m pytest, not a different installed application. First explain your plan briefly, then implement the requested change and run the checks. Do not copy the completed reference implementation.\n'
    (WORK / 'PASTE_INTO_CLAUDE.txt').write_text(prompt)
    print('Fresh starter prepared at:', APP)
    print('Next: open 02_Brownfield.code-workspace and follow README.md')
elif action in ('code', 'test', 'run'):
    if not APP.exists():
        raise SystemExit('First run: python3 live_build.py prepare')
    if action == 'code':
        assistant = sys.argv[2] if len(sys.argv) > 2 else 'claude'
        if assistant not in ('claude', 'codex') or not shutil.which(assistant):
            raise SystemExit('Choose an installed assistant: python3 live_build.py code claude OR codex')
        print('Developer workspace:', APP, flush=True)
        print('Paste the contents of live_build/PASTE_INTO_CLAUDE.txt into the assistant.', flush=True)
        raise SystemExit(subprocess.call([assistant], cwd=APP))
    if not PY.exists():
        raise SystemExit('Run python3 install.py before the workshop.')
    if action == 'test':
        command = [str(PY), '-m', 'pytest']
    else:
        load_config(sys.argv[2] if len(sys.argv) > 2 else None)
        if not os.getenv('HR_AGENT_MODEL'):
            raise SystemExit('Configure the model first with python3 configure.py.')
        command = [str(PY), '-m', 'hr_agent.cli']
    # Explicitly prioritize this newly built copy over the installed reference.
    env = {**os.environ, 'PYTHONUTF8': '1'}
    env['PYTHONPATH'] = str(APP)
    print('Using LIVE code:', APP, flush=True)
    raise SystemExit(subprocess.call(command, cwd=APP, env=env))
else:
    print('From the repository root: python3 live_build.py prepare | code [claude|codex] | test | run')
