# Copyright(C) 2026 Advanced Micro Devices, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
"""/quit and /reset report a failed session save instead of claiming success."""

from types import SimpleNamespace

from gaia_agent_chat import app


class _FakeAgent:
    def __init__(self, save_ok):
        self.save_ok = save_ok
        self.saves = 0
        self.current_session = SimpleNamespace(session_id="old")
        self.created = 0
        self.session_manager = SimpleNamespace(create_session=self._create)

    def _create(self):
        self.created += 1
        return SimpleNamespace(session_id="new")

    def save_current_session(self):
        self.saves += 1
        return self.save_ok


def _run(monkeypatch, capsys, agent, commands):
    inputs = iter(commands)
    monkeypatch.setattr("builtins.input", lambda *_: next(inputs))
    app.interactive_mode(agent)
    return capsys.readouterr().out


def test_quit_reports_failed_save(monkeypatch, capsys):
    agent = _FakeAgent(save_ok=False)
    out = _run(monkeypatch, capsys, agent, ["/quit"])
    assert "Failed to save session" in out
    assert "Goodbye!" in out


def test_quit_is_quiet_about_failure_when_save_works(monkeypatch, capsys):
    agent = _FakeAgent(save_ok=True)
    out = _run(monkeypatch, capsys, agent, ["/quit"])
    assert "Failed to save session" not in out
    assert "Goodbye!" in out


def test_reset_is_cancelled_when_save_fails(monkeypatch, capsys):
    agent = _FakeAgent(save_ok=False)
    out = _run(monkeypatch, capsys, agent, ["/reset", "/quit"])
    assert "reset cancelled" in out
    assert "Previous session saved" not in out
    assert agent.created == 0
    assert agent.current_session.session_id == "old"


def test_reset_proceeds_when_save_works(monkeypatch, capsys):
    agent = _FakeAgent(save_ok=True)
    out = _run(monkeypatch, capsys, agent, ["/reset", "/quit"])
    assert "Previous session saved" in out
    assert agent.created == 1
    assert agent.current_session.session_id == "new"
