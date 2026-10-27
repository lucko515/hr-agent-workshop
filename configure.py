"""Private model profiles. This loader never evaluates shell expressions."""
from pathlib import Path
import getpass
import json
import os
import sys
import warnings
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
KEYS = ('HR_AGENT_ENGINE', 'OPENAI_BASE_URL', 'OPENAI_API_KEY', 'ANTHROPIC_API_KEY',
        'HR_AGENT_MODEL', 'HR_AGENT_REASONING_EFFORT')


def config_path(profile=None):
    if profile is not None and profile not in ('api', 'local', 'claude'):
        raise SystemExit('Profile must be api, local or claude.')
    return ROOT / ('.env.' + profile if profile else '.env')


def parse_config(text):
    values = {}
    for number, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '=' not in line:
            raise ValueError(f'Invalid profile format on line {number}; rerun configure.py. Values are hidden.')
        key, value = line.split('=', 1)
        key, value = key.strip(), value.strip()
        if key not in KEYS:
            continue
        if value.startswith('"'):
            try:
                value = json.loads(value)
            except ValueError:
                raise ValueError(f'Invalid quoting on line {number}; rerun configure.py. Values are hidden.') from None
        elif value.startswith("'"):
            if not value.endswith("'") or len(value) < 2:
                raise ValueError(f'Invalid quoting on line {number}; rerun configure.py.')
            value = value[1:-1]
        else:
            value = value.split(' #', 1)[0].strip()
        if not isinstance(value, str):
            raise ValueError(f'Expected text on line {number}; rerun configure.py.')
        values[key] = value
    return values


def load_config(profile=None):
    path = config_path(profile)
    if profile is None and not path.exists():
        available = [p for p in ('api', 'claude', 'local') if config_path(p).exists()]
        if len(available) == 1:
            path = config_path(available[0])
        elif len(available) > 1:
            raise SystemExit('Choose a profile explicitly: app api, app claude or app local.')
    if profile and not path.exists():
        raise SystemExit(f'Configure this route privately first: python configure.py {profile} (see SETUP.md for your Python command).')
    if path.exists():
        try:
            values = parse_config(path.read_text(encoding='utf-8-sig'))
        except (OSError, ValueError) as exc:
            message = str(exc) if isinstance(exc, ValueError) and not isinstance(exc, UnicodeError) else 'Cannot read profile; recreate it with configure.py.'
            raise SystemExit(message) from None
        for key in KEYS:
            os.environ.pop(key, None)
        os.environ.update(values)


def hidden_key(prompt):
    # Never fall back to echoing a credential in an IDE output pane or redirected stdin.
    with warnings.catch_warnings():
        warnings.simplefilter('error', getpass.GetPassWarning)
        try:
            return getpass.getpass(prompt).strip()
        except getpass.GetPassWarning:
            raise SystemExit('Hidden input is unavailable. Run configure.py in Terminal or PowerShell, not an IDE output pane. No key was saved.') from None


def main():
    profile = sys.argv[1] if len(sys.argv) > 1 else None
    path = config_path(profile)
    route = {'api': '1', 'claude': '2', 'local': '3'}.get(profile)
    if not route:
        print('1 OpenAI-compatible API\n2 Anthropic API (Claude)\n3 Local Ollama\n4 Local LM Studio')
        route = input('Choose 1–4: ').strip()
    if route == '1':
        base = input('Base URL [https://api.openai.com/v1]: ').strip() or 'https://api.openai.com/v1'
        key = hidden_key('API key (hidden): ')
        default_model = 'gpt-4.1-mini' if base.rstrip('/') == 'https://api.openai.com/v1' else ''
        model = input(f'Model ID [{default_model or "provider model supporting function tools"}]: ').strip() or default_model
        values = dict(HR_AGENT_ENGINE='openai', OPENAI_BASE_URL=base, OPENAI_API_KEY=key, HR_AGENT_MODEL=model)
    elif route == '2':
        values = dict(HR_AGENT_ENGINE='claude', ANTHROPIC_API_KEY=hidden_key('Anthropic API key (hidden): '),
                      HR_AGENT_MODEL=input('Exact Claude model ID enabled on your API account: ').strip())
    elif route in ('3', '4'):
        base = 'http://127.0.0.1:11434/v1/' if route == '3' else 'http://127.0.0.1:1234/v1/'
        model = input('Installed model ID [qwen3:4b]: ').strip() or 'qwen3:4b'
        values = dict(HR_AGENT_ENGINE='openai', OPENAI_BASE_URL=base, OPENAI_API_KEY='local-demo', HR_AGENT_MODEL=model)
    else:
        raise SystemExit('No configuration changed.')
    if 'OPENAI_BASE_URL' in values:
        url = urlsplit(values['OPENAI_BASE_URL'])
        if url.scheme not in ('http', 'https') or not url.hostname or url.username or url.password or url.query or url.fragment:
            raise SystemExit('Use an http(s) base URL without embedded credentials, query or fragment. Nothing saved.')
    if any(not v for v in values.values()):
        raise SystemExit('Missing value. Nothing saved.')
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write('# Private configuration. Do not share or source in a shell.\n')
        for key, value in values.items():
            f.write(key + '=' + json.dumps(value) + '\n')
    path.chmod(0o600)
    suffix = f' {profile}' if profile else ''
    print('Saved privately. No credential was printed.')
    print(f'Check setup without spending API credit: python doctor.py{suffix}')
    print(f'Then run: python launch.py app{suffix} (use your chosen Python command).')


if __name__ == '__main__':
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        raise SystemExit('\nConfiguration cancelled. Existing profile preserved.')
