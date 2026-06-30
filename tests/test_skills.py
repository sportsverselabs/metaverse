"""Tests for the skill registry and draft-only safety guarantees."""

import pytest

from core.llm_router import LLMRouter
from core.policy import FORBIDDEN_ACTIONS
from skills.base import STATUS_DRAFT, DraftSkill, SkillSpec
from skills.registry import SkillRegistry, default_registry

EXPECTED_SKILLS = {
    "sports_topic_research_draft",
    "video_idea_draft",
    "script_outline_draft",
    "affiliate_product_research_draft",
    "compliance_review_draft",
    "daily_report_draft",
}


def test_default_registry_has_the_core_six_skills():
    # The original six are always present; department packs add more on top (see skills/packs.py).
    reg = default_registry()
    assert EXPECTED_SKILLS.issubset(set(reg.names()))


def test_department_pack_skills_registered():
    from skills.packs import ALL_PACK_SKILLS
    names = set(default_registry().names())
    assert {c.spec.name for c in ALL_PACK_SKILLS}.issubset(names)
    assert len(names) >= len(EXPECTED_SKILLS) + len(ALL_PACK_SKILLS)


def test_every_skill_is_draft_only_and_cannot_publish():
    reg = default_registry()
    for spec in reg.specs():
        assert spec.draft_only is True
        assert spec.requires_human_approval is True
        # Allowed actions must never include any forbidden (publishing/posting/etc.) action.
        assert set(spec.allowed_actions).isdisjoint(FORBIDDEN_ACTIONS)
        # The prohibited list must explicitly cover publishing.
        assert "publish" in spec.prohibited_actions


def test_registry_rejects_skill_with_forbidden_action():
    class BadSkill(DraftSkill):
        spec = SkillSpec(
            name="bad",
            purpose="tries to publish",
            allowed_actions=["create_draft", "publish"],
        )

        def build_prompt(self, payload):
            return "sys", "user"

    reg = SkillRegistry()
    with pytest.raises(ValueError):
        reg.register(BadSkill())


def test_draft_skill_runs_in_mock_mode():
    reg = default_registry()
    skill = reg.get("video_idea_draft")
    result = skill.run({"topic": "a buzzer beater"}, llm=LLMRouter())
    assert result.status == STATUS_DRAFT
    assert result.is_mock is True
    assert "DRAFT" in result.content
