"""Install the HR application dependencies once, before the workshop."""
from pathlib import Path
import os
import subprocess
import sys
import venv

ROOT = Path(__file__).resolve().parent
if sys.version_info < (3, 10):
    raise SystemExit('Python 3.10+ is required.')
choice = input('Engine dependencies: 1 API/local, 2 Claude SDK, 3 both [1]: ').strip() or '1'
extras = {'1': 'openai,dev', '2': 'claude,dev', '3': 'all,dev'}.get(choice)
if not extras:
    raise SystemExit('Choose 1, 2 or 3.')
venv.create(ROOT / '.venv', with_pip=True)
py = ROOT / '.venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
subprocess.run([str(py), '-m', 'pip', 'install', '-e', f'{ROOT / "agent"}[{extras}]'], check=True)
print('Installed. Next: choose a model profile in SETUP.md')
