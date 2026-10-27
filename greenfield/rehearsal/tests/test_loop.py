from types import SimpleNamespace as N
import json
import hr


def reply(name=None, args=None, text='Done.'):
    calls = [N(id='call_1', type='function', function=N(name=name, arguments=json.dumps(args)))] if name else []
    return N(choices=[N(message=N(content=None if name else text, tool_calls=calls))])


class FakeClient:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.seen = []
        self.chat = N(completions=N(create=self.create))
    def create(self, **kwargs):
        # Deep copy: the agent must not make the past appear correct by later mutation.
        self.seen.append(json.loads(json.dumps(kwargs)))
        return next(self.responses)


def test_tool_result_reenters_conversation(monkeypatch):
    monkeypatch.setenv('HR_AGENT_MODEL', 'scripted-test-model')
    client = FakeClient([reply('search_policies', {'query': 'annual leave'}), reply(text='25 days.')])
    result = hr.run_turn(client, hr.make_state(), 'How much annual leave?', lambda c: False)
    assert result == '25 days.' and len(client.seen) == 2
    second = client.seen[1]['messages']
    assert any(m['role'] == 'assistant' and m.get('tool_calls') for m in second)
    assert any(m['role'] == 'tool' and m['tool_call_id'] == 'call_1' and '25' in m['content'] for m in second)
    schemas = client.seen[0]['tools']
    assert {t['function']['name'] for t in schemas} == {'search_policies', 'request_leave', 'escalate_to_hr'}
    assert all('employee_id' not in t['function']['parameters'].get('properties', {}) for t in schemas)


def test_model_request_still_goes_through_human(monkeypatch):
    monkeypatch.setenv('HR_AGENT_MODEL', 'scripted-test-model')
    client = FakeClient([reply('request_leave', {'start_date': '2026-11-03', 'end_date': '2026-11-05'}), reply(text='Cancelled.')])
    state, cards = hr.make_state(), []
    def decline(card):
        cards.append(card); return False
    hr.run_turn(client, state, 'Book leave', decline)
    assert len(cards) == 1 and state['requests'] == []


def test_unknown_tool_returns_error_to_model(monkeypatch):
    monkeypatch.setenv('HR_AGENT_MODEL', 'scripted-test-model')
    client = FakeClient([reply('shell', {'command': 'not allowed'}), reply(text='Cannot do that.')])
    hr.run_turn(client, hr.make_state(), 'Run a command', lambda c: True)
    assert any(m['role'] == 'tool' and 'error' in m['content'].lower() for m in client.seen[1]['messages'])


def test_loop_has_a_call_limit(monkeypatch):
    monkeypatch.setenv('HR_AGENT_MODEL', 'scripted-test-model')
    client = FakeClient([reply('search_policies', {'query': 'annual'}) for _ in range(2)])
    result = hr.run_turn(client, hr.make_state(), 'Keep searching', lambda c: False, max_turns=2)
    assert len(client.seen) == 2 and any(word in result.lower() for word in ('limit', 'stopped', 'maximum'))
