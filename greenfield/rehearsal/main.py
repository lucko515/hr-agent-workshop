"""Interactive workshop CLI; configuration comes from the launcher environment."""

import json
import os

from providers import make_client

from hr import make_state, run_turn


def confirm(card):
    print(json.dumps(card, indent=2))
    try:
        return input('Store this leave request? [y/N] ').strip().lower() in {'y', 'yes'}
    except (EOFError, KeyboardInterrupt):
        print('\nRequest cancelled.')
        return False


def main():
    try:
        client = make_client()
    except (KeyError, ValueError, ImportError):
        print('Configure the selected provider and install its dependencies before running.')
        return

    state = make_state()
    print('HR workshop demo. Blank input shows records and exits.')
    print('Records are local and in memory. Pending leave does not reserve balance.')
    with client:
        while True:
            try:
                prompt = input('\nYou: ').strip()
            except (EOFError, KeyboardInterrupt):
                prompt = ''
            if not prompt:
                print(json.dumps(state, indent=2))
                break
            try:
                print(run_turn(client, state, prompt, confirm))
            except Exception as exc:
                print(f'Model request failed ({type(exc).__name__}). Check the selected provider privately.')


if __name__ == '__main__':
    main()
