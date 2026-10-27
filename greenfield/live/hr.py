"""Workshop starter: interface only. The coding agent implements these functions."""

def make_state():
    raise NotImplementedError('Build the fake employee session and empty records.')


def search_policies(query):
    raise NotImplementedError('Read the local policy and return grounded facts.')


def request_leave(state, start_date, end_date, confirm):
    raise NotImplementedError('Validate, ask the human, then store a pending request.')


def escalate_to_hr(state, summary):
    raise NotImplementedError('Store a minimal unresolved case for a human.')


def dispatch(name, arguments, state, confirm):
    raise NotImplementedError('Allow only the three named tools, validate arguments.')


def run_turn(client, state, prompt, confirm, max_turns=8):
    raise NotImplementedError('Call a real model with tools, execute requests, return results.')
