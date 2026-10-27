"""Claude protocol checks using scripted responses, never real API credentials."""
from types import SimpleNamespace as N
import json
import hr


class Block:
    def __init__(self, **values):
        self.values = values
    def model_dump(self, **kwargs):
        return self.values.copy()


def call(name, args, id='call_1'):
    return Block(type='tool_use', id=id, name=name, input=args)


def reply(*blocks, reason='tool_use'):
    return N(content=list(blocks), stop_reason=reason)


def done():
    return reply(Block(type='text', text='Finished.'), reason='end_turn')


class FakeClaude:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.seen = []
        self.messages = N(create=self.create)
    def create(self, **kwargs):
        self.seen.append(json.loads(json.dumps(kwargs)))
        return next(self.responses)


def setup(monkeypatch):
    monkeypatch.setenv('HR_AGENT_ENGINE', 'claude')
    monkeypatch.setenv('HR_AGENT_MODEL', 'scripted-claude-test')


def test_claude_parallel_results_and_unknown_tool(monkeypatch):
    setup(monkeypatch)
    client = FakeClaude([reply(call('search_policies', {'query': 'annual'}, 'a'),
                               call('shell', {'command': 'forbidden'}, 'b')), done()])
    assert hr.run_turn(client, hr.make_state(), 'Policy?', lambda c: False) == 'Finished.'
    req = client.seen[1]
    assert req['system'] and all(m['role'] != 'system' for m in req['messages'])
    assert {t['name'] for t in req['tools']} == {'search_policies', 'request_leave', 'escalate_to_hr'}
    assert all('input_schema' in t for t in req['tools'])
    assert req['messages'][-2]['role'] == 'assistant'
    results = req['messages'][-1]
    assert results['role'] == 'user'
    assert [b['tool_use_id'] for b in results['content']] == ['a', 'b']
    assert '25' in results['content'][0]['content']
    assert results['content'][1]['is_error'] is True


def test_claude_uses_the_same_confirmation_gate(monkeypatch):
    setup(monkeypatch)
    for approval in (False, True):
        state, cards = hr.make_state(), []
        def confirm(card):
            cards.append(card); return approval
        client = FakeClaude([reply(call('request_leave', {'start_date': '2026-11-03', 'end_date': '2026-11-05'})), done()])
        hr.run_turn(client, state, 'Book leave', confirm)
        assert len(cards) == 1 and len(state['requests']) == int(approval)
        if approval:
            assert state['requests'][0]['status'] == 'pending_manager_approval'


def test_claude_loop_has_a_call_limit(monkeypatch):
    setup(monkeypatch)
    client = FakeClaude([reply(call('search_policies', {'query': 'annual'})) for _ in range(2)])
    result = hr.run_turn(client, hr.make_state(), 'Search', lambda c: False, max_turns=2)
    assert len(client.seen) == 2 and 'limit' in result.lower()


def test_claude_truncated_tool_response_does_not_write(monkeypatch):
    setup(monkeypatch)
    state = hr.make_state()
    client = FakeClaude([reply(call('request_leave', {'start_date': '2026-11-03', 'end_date': '2026-11-05'}), reason='max_tokens')])
    result = hr.run_turn(client, state, 'Book leave', lambda c: True)
    assert not state['requests'] and 'limit' in result.lower()
