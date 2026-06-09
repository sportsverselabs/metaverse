"""End-to-end tests for the Hermes -> OpenClaw delegation pipeline and its safety gates.

These lock in the Phase 2A guarantees:
- Hermes classifies an NL task and delegates to OpenClaw.
- High-risk skills are blocked (at Sentinel and at OpenClaw).
- Compliance must run before a draft is marked ready for owner review.
- Every task is logged to memory.
- Nothing is ever published.
"""

from agents.base import (
    STATUS_BLOCKED,
    STATUS_ESCALATED,
    STATUS_READY_FOR_REVIEW,
    Task,
)
from agents.compliance import Compliance
from agents.hermes import Hermes
from agents.openclaw import OpenClaw
from agents.sentinel import Sentinel
from core.llm_router import LLMRouter
from core.policy import RISK_HIGH
from memory.manager import MemoryManager
from skills.base import DraftSkill, SkillSpec
from skills.registry import SkillRegistry, default_registry


def build_org(tmp_path, *, with_compliance=True):
    memory = MemoryManager(store_dir=tmp_path)
    llm = LLMRouter()  # mock mode
    shared = {"config": None, "memory": memory, "llm": llm}
    hermes = Hermes(**shared)
    hermes.register(OpenClaw(registry=default_registry(), **shared))
    hermes.register(Sentinel(**shared))
    if with_compliance:
        hermes.register(Compliance(**shared))
    return hermes, memory


def test_hermes_delegates_to_openclaw_and_marks_ready(tmp_path):
    hermes, _ = build_org(tmp_path)
    result = hermes.handle(Task(name="request", payload={"text": "please draft some video ideas about the finals"}))
    assert result.status == STATUS_READY_FOR_REVIEW
    assert result.data["skill"] == "video_idea_draft"
    assert result.data["published"] is False
    assert result.data["requires_human_approval"] is True
    assert result.data["draft"]
    # Compliance ran and attached a risk score + verdict.
    assert "risk_score" in result.data
    assert result.data["compliance"]["verdict"] == "needs_human_review"


def test_unmatched_task_is_escalated(tmp_path):
    hermes, _ = build_org(tmp_path)
    result = hermes.handle(Task(name="request", payload={"text": "order me a pizza"}))
    assert result.status == STATUS_ESCALATED


def test_compliance_required_before_owner_review(tmp_path):
    # No Compliance agent registered -> Hermes must NOT mark ready; it escalates.
    hermes, _ = build_org(tmp_path, with_compliance=False)
    result = hermes.handle(Task(name="request", payload={"text": "draft a daily report"}))
    assert result.status == STATUS_ESCALATED
    assert "Compliance" in result.detail


def test_memory_logs_the_task(tmp_path):
    hermes, memory = build_org(tmp_path)
    hermes.handle(Task(name="request", payload={"text": "draft a daily report"}))
    events = memory.read_events()
    assert "task_received" in events
    assert "daily_report_draft" in events
    assert "decision" in events


def test_sentinel_blocks_high_risk_skill(tmp_path):
    memory = MemoryManager(store_dir=tmp_path)
    sentinel = Sentinel(config=None, memory=memory, llm=None)
    spec = SkillSpec(name="risky", purpose="x", risk_level=RISK_HIGH, allowed_actions=["create_draft"])
    verdict = sentinel.review_skill(spec)
    assert verdict.allowed is False
    # The block was written to the memory audit trail.
    assert "sentinel_block" in memory.read_events()


def test_openclaw_blocks_high_risk_skill():
    class RiskySkill(DraftSkill):
        spec = SkillSpec(name="risky_draft", purpose="x", risk_level=RISK_HIGH, allowed_actions=["create_draft"])

        def build_prompt(self, payload):
            return "sys", "user"

    reg = SkillRegistry()
    reg.register(RiskySkill())  # registry allows it (draft-only, no forbidden actions)...
    claw = OpenClaw(registry=reg, llm=LLMRouter())
    result = claw.handle(Task(name="risky_draft"))  # ...but OpenClaw blocks high-risk at runtime.
    assert result.status == STATUS_BLOCKED
    assert "high-risk" in result.detail
