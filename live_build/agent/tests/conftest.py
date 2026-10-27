from datetime import date

import pytest

from hr_agent.db import seed
from hr_agent.tools import Session, build_tools

TODAY = date(2026, 10, 19)   # a Monday. Fixed so every run sees the same calendar.


@pytest.fixture
def db():
    return seed(TODAY)


@pytest.fixture
def ana(db):
    return Session("E001", db)


def tools_for(session):
    """Tool handlers by name, callable without any model: await tools['x']({...})."""
    return {t.name: t.handler for t in build_tools(session)}


def text_of(result) -> str:
    return result["content"][0]["text"]
