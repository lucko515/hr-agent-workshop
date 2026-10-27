"""Start the workshop's local Ollama server, or a normal installed Ollama."""
from pathlib import Path
import os
import shutil
import subprocess
import urllib.request

ROOT = Path(__file__).resolve().parent
try:
    with urllib.request.urlopen('http://127.0.0.1:11434/api/tags', timeout=2) as response:
        print('Ollama is already running on 127.0.0.1:11434. Use python3 launch.py app local.')
        raise SystemExit(0)
except (OSError, TimeoutError):
    pass
local = ROOT / '.runtime/ollama/0.40.6/libexec/ollama'
binary = str(local) if local.exists() else shutil.which('ollama')
if not binary:
    raise SystemExit('Install Ollama from https://ollama.com/download, download a tool-capable model, then rerun. See SETUP.md.')
env = os.environ.copy()
env['OLLAMA_HOST'] = '127.0.0.1:11434'
env['OLLAMA_CONTEXT_LENGTH'] = '8192'
if local.exists():
    env['OLLAMA_MODELS'] = str(ROOT / '.runtime/models')
print('Leave this terminal open. In another terminal: python3 launch.py app local', flush=True)
raise SystemExit(subprocess.call([binary, 'serve'], env=env))
