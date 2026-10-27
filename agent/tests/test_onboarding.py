"""Offline contract for the structured, read-only onboarding lookup."""
from copy import deepcopy

import pytest

from hr_agent import policy_search
from hr_agent.agent import TOOL_TIERS, Trace, decide
from hr_agent.tools import build_tools
from .conftest import text_of, tools_for


async def test_week_one_exact_policy_and_source(ana):
    result = await tools_for(ana)["get_onboarding_checklist"]({"stage": "week_one"})
    assert not result["is_error"]
    assert text_of(result) == (
        "[Onboarding Checklist | section: Week one | version 1.8, effective 2026-05-01]\n"
        "Collect your laptop from IT, complete security training within 5 working days, "
        "set up two-factor authentication, and meet your onboarding buddy."
    )


@pytest.mark.parametrize("stage", ["week_two", "", None, [], {}])
async def test_invalid_stage_is_useful_error(ana, stage):
    result = await tools_for(ana)["get_onboarding_checklist"]({"stage": stage})
    assert result["is_error"]
    assert all(s in text_of(result) for s in ("before_day_one", "week_one", "first_month"))


async def test_lookup_never_mutates_hr_data(ana):
    before = deepcopy(vars(ana.db))
    lookup = tools_for(ana)["get_onboarding_checklist"]
    for stage in ("before_day_one", "week_one", "first_month", "unsupported"):
        await lookup({"stage": stage})
    assert vars(ana.db) == before


async def test_missing_section_uses_loader_and_returns_error(ana, monkeypatch):
    monkeypatch.setattr(policy_search, "load_sections", lambda: [])
    result = await tools_for(ana)["get_onboarding_checklist"]({"stage": "week_one"})
    assert result["is_error"]
    assert "Week one" in text_of(result) and "unavailable" in text_of(result).lower()


async def test_registration_schema_and_tier(ana):
    spec = {t.name: t for t in build_tools(ana)}["get_onboarding_checklist"]
    assert spec.input_schema == {
        "type": "object",
        "properties": {"stage": {"type": "string", "enum": ["before_day_one", "week_one", "first_month"]}},
        "required": ["stage"],
        "additionalProperties": False,
    }
    assert TOOL_TIERS[spec.name] == 1

    async def never_confirm(card):
        pytest.fail("Read-only lookup must not ask for confirmation")

    assert await decide(ana, spec.name, {"stage": "week_one"}, never_confirm, Trace()) is None
