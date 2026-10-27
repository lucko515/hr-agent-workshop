"""One entry point: native subscription agents or the HR application."""
from pathlib import Path
import os
import shutil
import subprocess
import sys
from configure import load_config

ROOT = Path(__file__).resolve().parent
PY = ROOT / '.venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
route = sys.argv[1] if len(sys.argv) > 1 else ''
if route in ('codex', 'claude'):
    if not shutil.which(route):
        raise SystemExit(f'{route} is not installed. See SETUP.md.')
    command = [route, '-s', 'workspace-write', '--no-alt-screen'] if route == 'codex' else [route]
    raise SystemExit(subprocess.call(command, cwd=ROOT / 'native'))
if route in ('app', 'verify', 'tests'):
    if not PY.exists():
        raise SystemExit('Prepare dependencies first: python3 install.py')
    load_config(sys.argv[2] if len(sys.argv) > 2 else None)
    if route == 'tests':
        args = ['-m', 'pytest']
    elif route == 'verify':
        args = [str(ROOT / 'verify_live.py')]
    else:
        if not os.getenv('HR_AGENT_MODEL'):
            raise SystemExit('Select credentials/model first: python3 configure.py')
        print('Model:', os.getenv('HR_AGENT_MODEL'), '| engine:', os.getenv('HR_AGENT_ENGINE'), flush=True)
        args = ['-m', 'hr_agent.cli']
    raise SystemExit(subprocess.call([str(PY), *args], cwd=ROOT / 'agent'))
print('Run from this folder:\n  python3 launch.py codex   # ChatGPT subscription\n  python3 launch.py claude  # Claude Code subscription\n  python3 configure.py     # API key or local endpoint setup\n  python3 launch.py app     # Real HR application\n  python3 launch.py verify  # Real-model acceptance checks\n  python3 launch.py tests   # Offline tests')
