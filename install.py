"""Install into this checkout's environment; activation is never required."""
from pathlib import Path
import argparse
import os
import subprocess
import sys
import venv

ROOT = Path(__file__).resolve().parent
EXTRAS = {'api': 'openai,dev', 'local': 'openai,dev', 'claude': 'claude,dev', 'all': 'all,dev'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine', choices=EXTRAS, default='all', help='default: all; local/api avoid the Claude SDK download')
    args = parser.parse_args()
    if sys.version_info < (3, 10):
        raise SystemExit('Python 3.10+ is required. This command selected Python ' + sys.version.split()[0] +
                         '. Install Python 3.12 and use py -3.12 install.py (Windows) or python3.12 install.py (macOS/Linux). See SETUP.md.')
    print('Python:', sys.version.split()[0], '| environment:', ROOT / '.venv', flush=True)
    py = ROOT / '.venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    if py.exists():
        try:
            check = subprocess.run([str(py), '-c', 'import sys; raise SystemExit(sys.version_info < (3,10))'], capture_output=True)
        except OSError:
            check = None
        if check is None or check.returncode:
            raise SystemExit('Existing .venv cannot run with Python 3.10+. Rename .venv to .venv-old, then rerun this installer. Your code and profiles are preserved.')
    try:
        # Symlinks preserve shared-library lookup for standalone Python distributions on macOS.
        if not py.exists():
            venv.create(ROOT / '.venv', with_pip=True, symlinks=os.name != 'nt')
        subprocess.run([str(py), '-m', 'pip', '--version'], check=True, capture_output=True)
    except (OSError, subprocess.CalledProcessError):
        raise SystemExit('Could not create a working environment with pip. On Debian/Ubuntu install the matching python3-venv package. Otherwise repair/install Python 3.12. Rename an incomplete .venv before retrying. See SETUP.md.')
    print('Installing', args.engine, 'dependencies (internet access required)...', flush=True)
    result = subprocess.run([str(py), '-m', 'pip', 'install', '--disable-pip-version-check', '-e',
                             f'{ROOT / "agent"}[{EXTRAS[args.engine]}]'], capture_output=True, text=True, encoding='utf-8', errors='replace')
    if result.returncode:
        # Package-manager output can include authenticated corporate index/proxy URLs.
        output = (result.stdout + result.stderr).lower()
        hint = 'Check internet access and your approved package index/proxy.'
        if 'certificate' in output or 'ssl' in output:
            hint = 'Package download certificate check failed. Ask IT for your approved proxy/certificate configuration; do not disable TLS verification.'
        elif 'no matching distribution' in output or 'could not find a version' in output:
            hint = 'Your package index has no compatible dependency version. Check Python 3.10+, 64-bit OS, and your approved package mirror. Try --engine local if Claude SDK wheels are unavailable.'
        raise SystemExit('Installation failed. ' + hint + '\nNo credentials or package-manager logs were printed. See SETUP.md troubleshooting.')
    check = subprocess.run([str(py), '-m', 'pip', 'check'], capture_output=True)
    if check.returncode:
        raise SystemExit('Dependency conflict detected. Rename .venv to .venv-old and reinstall with this same Python. Your code and profiles are preserved.')
    print('Installed successfully. Next: python doctor.py, then choose ONE route in SETUP.md.')
    print('Use the same Python command you used for this installer. No venv activation needed.')


if __name__ == '__main__':
    main()
