"""Shared pytest fixtures.

Tools call the module-level ``reaper_call`` to reach REAPER. We monkeypatch that
single function with a recorder, so every tool can be exercised without REAPER (or the
bridge) running — we assert on the (func, args) the tool would have sent and on how it
handles the response.
"""

import sys
from pathlib import Path

import pytest

# reaper_mcp_server.py lives at the repo root, one level up from tests/.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import reaper_mcp_server as srv  # noqa: E402


class Recorder:
    """Stand-in for reaper_call: records calls and returns a canned response."""

    def __init__(self, response=None):
        self.calls = []
        self.response = response if response is not None else {"ok": True, "ret": 0}

    async def __call__(self, func, *args):
        self.calls.append((func, list(args)))
        return self.response

    @property
    def last(self):
        assert self.calls, "no reaper_call was made"
        return self.calls[-1]


@pytest.fixture
def reaper(monkeypatch):
    """Patch reaper_call with a Recorder and hand it to the test."""
    rec = Recorder()
    monkeypatch.setattr(srv, "reaper_call", rec)
    return rec
