import copy
import json
import hr


def test_session_identity_and_balance():
    state = hr.make_state()
    assert state == {'employee_id': 'E001', 'balance': 12, 'requests': [], 'cases': []}


def test_policy_comes_with_facts_and_source():
    result = json.dumps(hr.search_policies('annual leave entitlement')).lower()
    for fact in ('25', 'annual leave policy', 'entitlement', '1.0'):
        assert fact in result


def test_yes_means_pending_not_approved():
    state, cards = hr.make_state(), []
    def approve(card):
        cards.append(str(card)); return True
    hr.request_leave(state, '2026-11-03', '2026-11-05', approve)
    assert len(cards) == 1 and '2026-11-03' in cards[0] and '2026-11-05' in cards[0]
    assert len(state['requests']) == 1
    record = state['requests'][0]
    assert record['employee_id'] == 'E001'
    assert (record['start_date'], record['end_date'], record['days']) == ('2026-11-03', '2026-11-05', 3)
    assert record['status'] == 'pending_manager_approval'


def test_no_means_no_write():
    state = hr.make_state(); before = copy.deepcopy(state)
    hr.request_leave(state, '2026-11-03', '2026-11-05', lambda card: False)
    assert state == before


def test_invalid_dates_never_reach_confirmation():
    for start, end in [('wrong', '2026-11-05'), ('2026-11-05', '2026-11-03'),
                       ('2026-10-01', '2026-10-02'), ('2026-11-07', '2026-11-08'),
                       ('2026-11-02', '2026-11-30')]:
        state = hr.make_state(); before = copy.deepcopy(state)
        def forbidden(card):
            raise AssertionError('Invalid requests must not reach approval')
        assert 'error' in hr.request_leave(state, start, end, forbidden)
        assert state == before


def test_duplicate_does_not_write_or_confirm_twice():
    state, cards = hr.make_state(), []
    def approve(card):
        cards.append(card); return True
    for _ in range(2):
        hr.request_leave(state, '2026-11-03', '2026-11-05', approve)
    assert len(state['requests']) == 1 and len(cards) == 1


def test_escalation_records_case_without_leave():
    state = hr.make_state()
    hr.escalate_to_hr(state, 'Employee asks HR to identify the leave category.')
    assert len(state['cases']) == 1 and not state['requests']
    assert 'category' in json.dumps(state['cases'])


def test_model_cannot_choose_identity_or_bypass_gate():
    state = hr.make_state()
    for extra in ({'employee_id': 'E002'}, {'approved': True}):
        result = hr.dispatch('request_leave', {'start_date': '2026-11-03', 'end_date': '2026-11-05', **extra}, state, lambda c: True)
        assert 'error' in result and not state['requests']


def test_unknown_tool_missing_args_and_empty_escalation_are_errors():
    state = hr.make_state()
    for name, args in [('shell', {'command': 'echo hi'}), ('request_leave', {}),
                       ('escalate_to_hr', {'summary': ''}), ('search_policies', {})]:
        assert 'error' in hr.dispatch(name, args, state, lambda c: True)
    assert not state['requests'] and not state['cases']
