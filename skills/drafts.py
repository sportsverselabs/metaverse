"""The initial safe, draft-only skills.

All six produce drafts/reports only. Their specs declare ``draft_only=True``,
``requires_human_approval=True``, and allowed_actions that never intersect
``core.policy.FORBIDDEN_ACTIONS``. None may publish, post, email externally, buy,
upload, or modify production code.
"""

from __future__ import annotations

from core.policy import RISK_LOW, RISK_MEDIUM
from skills.base import DraftSkill, SkillSpec

_SYSTEM = (
    "You are a Sportsverse OS draft assistant for the faceless sports-media brand "
    "'Platinum Clips'. Produce a DRAFT only. Never publish, post, email, purchase, or "
    "upload anything. Flag anything that may need compliance review. Keep it brand-safe."
)


class SportsTopicResearchDraft(DraftSkill):
    spec = SkillSpec(
        name="sports_topic_research_draft",
        purpose="Draft a shortlist of trending/relevant sports topics to consider covering.",
        risk_level=RISK_LOW,
        allowed_actions=["create_draft", "research_public_info", "summarize"],
        triggers=["sports topic", "topic research", "research topic", "trending sports", "what to cover"],
    )

    def build_prompt(self, payload):
        focus = payload.get("focus", "general sports")
        return _SYSTEM, (
            f"Draft 5-8 candidate sports topics for short-form faceless videos about: {focus}. "
            "For each: a one-line hook, why it may trend, and any compliance/copyright caution. "
            "This is a draft for the owner to review — do not finalise or post."
        )


class VideoIdeaDraft(DraftSkill):
    spec = SkillSpec(
        name="video_idea_draft",
        purpose="Draft faceless short-form video ideas with hooks and angles.",
        risk_level=RISK_LOW,
        allowed_actions=["create_draft", "summarize"],
        triggers=["video idea", "video ideas", "content idea", "brainstorm video"],
    )

    def build_prompt(self, payload):
        topic = payload.get("topic", "a trending sports moment")
        return _SYSTEM, (
            f"Draft 5 faceless short-form video ideas about: {topic}. For each give a title, "
            "a 1-2 sentence hook, and the visual angle. Draft only — owner reviews before any use."
        )


class ScriptOutlineDraft(DraftSkill):
    spec = SkillSpec(
        name="script_outline_draft",
        purpose="Draft a short-form video script OUTLINE (not a final script).",
        risk_level=RISK_LOW,
        allowed_actions=["create_draft", "outline"],
        triggers=["script outline", "outline a script", "video script", "script for"],
    )

    def build_prompt(self, payload):
        topic = payload.get("topic", "a sports highlight")
        return _SYSTEM, (
            f"Draft a 30-45s faceless video script OUTLINE about: {topic}. Use beats: hook, "
            "build, payoff, CTA. Keep it an outline, not a finished script. Draft only."
        )


class AffiliateProductResearchDraft(DraftSkill):
    spec = SkillSpec(
        name="affiliate_product_research_draft",
        purpose="Draft a shortlist of potential affiliate product categories to research further.",
        risk_level=RISK_MEDIUM,  # touches monetisation; still draft-only, never buys/links live
        allowed_actions=["create_draft", "research_public_info", "summarize"],
        triggers=["affiliate", "affiliate product", "product research", "monetize", "products to promote"],
    )

    def build_prompt(self, payload):
        niche = payload.get("niche", "sports fans / sports content viewers")
        return _SYSTEM, (
            f"Draft 5 potential affiliate product CATEGORIES relevant to: {niche}. For each note "
            "the audience fit and a reminder that FTC/affiliate disclosure is required. Do NOT add "
            "real affiliate links or make purchases. Draft for owner review only."
        )


class ComplianceReviewDraft(DraftSkill):
    spec = SkillSpec(
        name="compliance_review_draft",
        purpose="Draft a plain-language compliance assessment of a piece of content.",
        risk_level=RISK_LOW,
        allowed_actions=["create_draft", "assess_content", "summarize"],
        triggers=["compliance review", "review compliance", "is this allowed", "compliance check"],
    )

    def build_prompt(self, payload):
        content = payload.get("content", "(no content provided)")
        return _SYSTEM, (
            "Draft a compliance assessment for the following content across: platform policy, "
            "copyright, fair use, affiliate/FTC disclosure, and brand safety. List concerns and "
            "suggested fixes. This is advisory only; a human makes the final call.\n\n"
            f"CONTENT:\n{content}"
        )


class DailyReportDraft(DraftSkill):
    spec = SkillSpec(
        name="daily_report_draft",
        purpose="Draft an internal daily status/intelligence report for the owner.",
        risk_level=RISK_LOW,
        allowed_actions=["create_draft", "write_report", "summarize"],
        triggers=["daily report", "daily summary", "status report", "report draft"],
    )

    def build_prompt(self, payload):
        notes = payload.get("notes", "(no notes supplied)")
        return _SYSTEM, (
            "Draft a concise internal daily report for the owner with sections: Done, In Progress, "
            "Risks/Blockers, Suggested Next Steps. This is an internal draft for owner review only "
            "(not emailed or posted).\n\n"
            f"INPUT NOTES:\n{notes}"
        )


# All initial skills, in registration order.
ALL_DRAFT_SKILLS = [
    SportsTopicResearchDraft,
    VideoIdeaDraft,
    ScriptOutlineDraft,
    AffiliateProductResearchDraft,
    ComplianceReviewDraft,
    DailyReportDraft,
]
