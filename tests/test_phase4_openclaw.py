"""OpenClaw skill agent: allowlist blocking + security warnings + logging."""

from agents.openclaw_skill_agent import OpenClawSkillAgent
from memory.manager import MemoryManager
from orchestration.state import OrchestrationState


def test_allowlisted_skill_is_allowed():
    agent = OpenClawSkillAgent()
    ok, _ = agent.is_allowed("daily_report_draft")
    assert ok is True


def test_unknown_skill_blocked_by_default():
    agent = OpenClawSkillAgent()
    ok, why = agent.is_allowed("delete_production_database")
    assert ok is False
    assert "allowlist" in why


def test_blocked_skill_emits_security_warning_and_does_not_run(tmp_path):
    memory = MemoryManager(store_dir=tmp_path / "mem")
    agent = OpenClawSkillAgent(memory=memory)
    state = OrchestrationState(user_request="run a skill", requested_skill="shell_exec")
    agent.run(state)
    assert state.final_status == "blocked_unapproved_skill"
    assert any("SECURITY WARNING" in w for w in state.security_warnings)
    # The blocked invocation is audited.
    assert "openclaw_skill_invocation" in memory.read_audit()


def test_allowed_skill_runs_draft_only(tmp_path):
    memory = MemoryManager(store_dir=tmp_path / "mem")
    agent = OpenClawSkillAgent(memory=memory)
    state = OrchestrationState(user_request="run a skill", requested_skill="daily_report_draft")
    agent.run(state)
    assert state.final_status.startswith("skill_ran")
    assert state.output  # produced a draft
