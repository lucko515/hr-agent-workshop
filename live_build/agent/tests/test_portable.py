"""Fast tests for the OpenAI-compatible engine, with a scripted fake model. No network, no key.

The fake plays the model's part: it returns the tool requests we script, and records what it was sent.
That tests our side of the loop: the gate, the tools, the conversation we build, the limits.
"""
import json
from types import SimpleNamespace as NS

import pytest

from hr_agent.agent import TOOL_TIERS, Trace
from hr_agent.portable import MAX_TURNS, new_conversation, run_turn

DATES = {"start_date": "2026-11-03", "end_date": "2026-11-05"}


def call(name, args, i=0):
    raw = args if isinstance(args, str) else json.dumps(args)
    return NS(id=f"call_{i}_{name}", type="function", function=NS(name=name, arguments=raw))


class FakeModel:
    """Each script step is a list of tool calls, or a string for the final answer."""
    def __init__(self, *steps):
        self.steps, self.sent = list(steps), []
        self.chat = NS(completions=NS(create=self.create))

    async def create(self, **kwargs):
        self.sent.append(json.loads(json.dumps(kwargs, default=str)))
        step = self.steps.pop(0) if self.steps else [("search_policies", {"query": "again"})]
        if isinstance(step, str):
            message = NS(content=step, tool_calls=None)
        else:
            message = NS(content=None, tool_calls=[call(n, a, i) for i, (n, a) in enumerate(step)])
        return NS(choices=[NS(message=message)], usage=NS(total_tokens=100))


async def run(fake, session, approve=True):
    async def approver(card): return approve
    trace = Trace()
    messages = new_conversation()
    await run_turn(fake, "test-model", session, messages, "I'd like 3 to 5 November off.", approver, trace)
    return trace, messages


async def test_happy_path_checks_asks_and_writes_once(ana):
    fake = FakeModel([("get_my_leave_balance", {})], [("check_leave_request", DATES)],
                     [("submit_leave_request", DATES)], "Done: LR-1003, your manager decides.")
    trace, messages = await run(fake, ana)
    assert [n for n, _ in trace.tool_calls] == ["get_my_leave_balance", "check_leave_request", "submit_leave_request"]
    assert len(trace.confirmations) == 1 and "12 -> 9" in trace.confirmations[0]
    assert [(r.reference, r.status) for r in ana.db.requests[2:]] == [("LR-1003", "pending_manager_approval")]
    assert trace.text.startswith("Done") and trace.turns == 4 and trace.tokens == 400 and trace.error is None

    first = fake.sent[0]
    assert first["model"] == "test-model" and first["messages"][0]["role"] == "system"
    assert {t["function"]["name"] for t in first["tools"]} == set(TOOL_TIERS)          # every HR tool, nothing else
    tool_results = [m["content"] for m in messages if m["role"] == "tool"]
    assert "Submitted: LR-1003" in tool_results[-1]


async def test_declined_card_writes_nothing_and_tells_the_model(ana):
    fake = FakeModel([("submit_leave_request", DATES)], "OK, nothing was submitted.")
    trace, messages = await run(fake, ana, approve=False)
    assert len(ana.db.requests) == 2 and len(trace.confirmations) == 1
    assert "The employee said no" in [m for m in messages if m["role"] == "tool"][0]["content"]


async def test_unknown_tool_and_bad_json_are_refused_with_a_reason(ana):
    fake = FakeModel([("delete_all_records", {})], [("check_leave_request", "{not json")], "Sorry.")
    trace, messages = await run(fake, ana)
    results = [m["content"] for m in messages if m["role"] == "tool"]
    assert "not available" in results[0] and "not valid JSON" in results[1]
    assert [a["allowed"] for a in ana.db.audit] == [False]                 # bad JSON never reached the gate


async def test_the_loop_stops_at_the_turn_limit(ana):
    trace, _ = await run(FakeModel(), ana)                                  # a model that never stops calling tools
    assert trace.turns == MAX_TURNS and "stopped after" in trace.error


async def test_only_the_settings_every_provider_accepts_are_sent(ana, monkeypatch):
    fake = FakeModel("Hi.")
    await run(fake, ana)
    assert set(fake.sent[0]) == {"model", "messages", "tools"}             # no temperature, no tool_choice
    monkeypatch.setenv("HR_AGENT_REASONING_EFFORT", "none")
    fake = FakeModel("Hi.")
    await run(fake, ana)
    assert fake.sent[0]["reasoning_effort"] == "none"


def test_engine_selection(monkeypatch):
    from hr_agent import engines
    monkeypatch.setenv("HR_AGENT_ENGINE", "openai")
    from hr_agent.portable import ask as portable_ask
    assert engines.get_ask() is portable_ask
    monkeypatch.setenv("HR_AGENT_ENGINE", "gemini")
    with pytest.raises(SystemExit):
        engines.engine()
