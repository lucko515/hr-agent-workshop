"""Local setup diagnostics. Never prints keys or calls a paid model."""
from pathlib import Path
import argparse
import importlib.util
import json
import os
import subprocess
import sys
import urllib.request
from configure import load_config

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('profile', nargs='?', choices=['api', 'claude', 'local'])
    parser.add_argument('--inside', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    py = ROOT / '.venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    if not args.inside:
        if not py.exists():
            raise SystemExit('FAIL: .venv is missing. Run install.py using Python 3.10+; see SETUP.md.')
        try:
            result = subprocess.run([str(py), str(Path(__file__).resolve()), *([args.profile] if args.profile else []), '--inside'],
                                    env={**os.environ, 'PYTHONUTF8': '1'})
        except OSError:
            raise SystemExit('FAIL: .venv cannot start. Rename it to .venv-old and rerun install.py.')
        raise SystemExit(result.returncode)
    print('Python:', sys.version.split()[0], '| OS:', sys.platform)
    if sys.version_info < (3, 10):
        raise SystemExit('FAIL: Python 3.10+ required. Recreate .venv with Python 3.12.')
    failures = []
    required = ['pytest', 'pytest_asyncio']
    if args.profile:
        load_config(args.profile)
        required += ['claude_agent_sdk', 'anthropic'] if os.getenv('HR_AGENT_ENGINE') == 'claude' else ['openai']
    for name in required:
        if importlib.util.find_spec(name) is None:
            failures.append('Missing ' + name + ': rerun install.py with --engine ' + (args.profile or 'all'))
    if args.profile:
        key = 'ANTHROPIC_API_KEY' if os.getenv('HR_AGENT_ENGINE') == 'claude' else 'OPENAI_API_KEY'
        if not os.getenv(key) or not os.getenv('HR_AGENT_MODEL'):
            failures.append('Incomplete profile: rerun configure.py ' + args.profile)
        print('Profile:', args.profile, '(values hidden)')
    if args.profile == 'local':
        try:
            # Only contact the built-in loopback Ollama server, never a profile-supplied URL.
            with urllib.request.urlopen('http://127.0.0.1:11434/api/tags', timeout=3) as response:
                names = {m['name'] for m in json.load(response).get('models', [])}
            model = os.getenv('HR_AGENT_MODEL', '')
            if model not in names and model + ':latest' not in names:
                failures.append('Configured model is not installed. Run ollama list, then ollama pull MODEL; configure.py local must use that exact model name.')
            else:
                print('Ollama is reachable and the configured model is installed.')
        except (OSError, ValueError, KeyError, TypeError):
            failures.append('Ollama is not ready. Open the Ollama app or run local_server.py in another terminal, then download the model.')
    if failures:
        for item in failures:
            print('FAIL:', item)
        return 1
    print('PASS: local setup checks. No model inference or paid API request was made.')
    if not args.profile:
        print('Next: configure.py api, claude or local, then doctor.py with that profile.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
