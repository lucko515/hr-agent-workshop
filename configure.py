"""Private model profiles. This loader never evaluates shell expressions."""
from pathlib import Path
import getpass
import json
import os
import sys

ROOT = Path(__file__).resolve().parent
KEYS = ('HR_AGENT_ENGINE', 'OPENAI_BASE_URL', 'OPENAI_API_KEY', 'ANTHROPIC_API_KEY',
        'HR_AGENT_MODEL', 'HR_AGENT_REASONING_EFFORT')


def config_path(profile=None):
    if profile is not None and profile not in ('api', 'local', 'claude'):
        raise SystemExit('Profile must be api, local or claude.')
    return ROOT / ('.env.' + profile if profile else '.env')


def load_config(profile=None):
    path = config_path(profile)
    if profile and not path.exists():
        raise SystemExit(f'Configure this route privately first: python3 configure.py {profile}')
    if path.exists():
        values = {}
        for line in path.read_text().splitlines():
            if line.strip() and not line.startswith('#'):
                key, value = line.split('=', 1)
                if key in KEYS:
                    values[key] = json.loads(value)
        # Switching provider must not inherit the previous endpoint or reasoning option.
        for key in KEYS:
            os.environ.pop(key, None)
        os.environ.update(values)


def main():
    profile = sys.argv[1] if len(sys.argv) > 1 else None
    path = config_path(profile)
    route = {'api': '1', 'claude': '2', 'local': '3'}.get(profile)
    if not route:
        print('1 OpenAI-compatible API\n2 Anthropic API (Claude)\n3 Local Ollama\n4 Local LM Studio')
        route = input('Choose 1–4: ').strip()
    if route == '1':
        base = input('Base URL [https://api.openai.com/v1]: ').strip() or 'https://api.openai.com/v1'
        key = getpass.getpass('API key (hidden): ').strip()
        default_model = 'gpt-4.1-mini' if base.rstrip('/') == 'https://api.openai.com/v1' else ''
        model = input(f'Model ID [{default_model or "provider model supporting function tools"}]: ').strip() or default_model
        values = dict(HR_AGENT_ENGINE='openai', OPENAI_BASE_URL=base, OPENAI_API_KEY=key, HR_AGENT_MODEL=model)
    elif route == '2':
        values = dict(HR_AGENT_ENGINE='claude', ANTHROPIC_API_KEY=getpass.getpass('Anthropic API key (hidden): ').strip(),
                      HR_AGENT_MODEL=input('Exact Claude model ID enabled on your API account: ').strip())
    elif route in ('3', '4'):
        base = 'http://127.0.0.1:11434/v1/' if route == '3' else 'http://127.0.0.1:1234/v1/'
        model = input('Installed model ID [qwen3:4b]: ').strip() or 'qwen3:4b'
        values = dict(HR_AGENT_ENGINE='openai', OPENAI_BASE_URL=base, OPENAI_API_KEY='local-demo', HR_AGENT_MODEL=model)
    else:
        raise SystemExit('No configuration changed.')
    if any(not v for v in values.values()):
        raise SystemExit('Missing value. Nothing saved.')
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w') as f:
        f.write('# Private configuration. Do not share or source in a shell.\n')
        for key, value in values.items():
            f.write(key + '=' + json.dumps(value) + '\n')
    path.chmod(0o600)
    suffix = f' {profile}' if profile else ''
    print('Saved privately. No credential was printed.')
    print(f'Check the real model: python3 launch.py verify{suffix}')


if __name__ == '__main__':
    main()
