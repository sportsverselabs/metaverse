"""Tests for agent registration and the publishing safety default."""

from agents.base import STATUS_BLOCKED, Task
from agents.hermes import Hermes
from agents.openclaw import OpenClaw
from agents.sentinel import Sentinel


def test_register_under_hermes():
    hermes = Hermes()
    claw = OpenClaw()
    hermes.register(claw)
    assert "openclaw" in hermes.agents
    assert claw.reports_to == "hermes"


def test_publishing_is_disabled_by_default():
    for agent in (Hermes(), OpenClaw(), Sentinel()):
        assert agent.can_publish_directly is False


def test_openclaw_blocks_unregistered_skill():
    # Empty registry -> nothing is whitelisted.
    claw = OpenClaw()
    result = claw.handle(Task(name="ghost_skill"))
    assert result.status == STATUS_BLOCKED
    assert "not whitelisted" in result.detail
