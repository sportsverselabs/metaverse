"""Department skill packs.

Skills are organized by department (not as random one-off skills). Each pack is a list of draft-only
skills a department's Hermes role can use via OpenClaw. All skills here are draft-only and never publish,
post, email, buy, upload, or modify code — same contract as ``skills/drafts.py``. New skills must also be
allowlisted in ``config/openclaw_allowlist.json`` before OpenClaw will run them.

See architecture/DEPARTMENT_SKILL_MAP.md.
"""

from __future__ import annotations

from core.policy import RISK_LOW, RISK_MEDIUM
from skills.base import DraftSkill, SkillSpec
from skills.drafts import (AffiliateProductResearchDraft, ComplianceReviewDraft, DailyReportDraft,
                           ScriptOutlineDraft, SportsTopicResearchDraft, VideoIdeaDraft)

_SYSTEM = (
    "You are a Sportsverse OS department draft assistant. Produce a DRAFT only. Never publish, post, "
    "email, purchase, or upload anything. Never invent scores, stats, or quotes. Flag anything that may "
    "need compliance review. Keep it brand-safe."
)


# ---- Creative department --------------------------------------------- #
class ThumbnailConceptDraft(DraftSkill):
    spec = SkillSpec(name="thumbnail_concept_draft",
                     purpose="Draft thumbnail concepts (layout, text, focal point) for a video.",
                     risk_level=RISK_LOW, allowed_actions=["create_draft", "summarize"],
                     triggers=["thumbnail", "thumbnail idea", "cover image"])

    def build_prompt(self, payload):
        topic = payload.get("topic", "a sports highlight")
        return _SYSTEM, (f"Draft 3 thumbnail concepts for a video about: {topic}. For each give the big "
                         "text (<=4 words), the focal image, and the color mood. Draft only.")


class TitleCardCopyDraft(DraftSkill):
    spec = SkillSpec(name="title_card_copy_draft",
                     purpose="Draft on-screen title-card / lower-third copy for a video.",
                     risk_level=RISK_LOW, allowed_actions=["create_draft", "summarize"],
                     triggers=["title card", "lower third", "on-screen text"])

    def build_prompt(self, payload):
        topic = payload.get("topic", "a sports moment")
        return _SYSTEM, (f"Draft 5 short on-screen title-card lines for a video about: {topic}. "
                         "Each <=6 words, punchy, brand-safe. Draft only.")


# ---- Marketing department -------------------------------------------- #
class SeoHashtagDraft(DraftSkill):
    spec = SkillSpec(name="seo_hashtag_draft",
                     purpose="Draft SEO keywords + hashtag sets per platform for a topic.",
                     risk_level=RISK_LOW, allowed_actions=["create_draft", "summarize"],
                     triggers=["seo", "hashtags", "keywords", "tags for"])

    def build_prompt(self, payload):
        topic = payload.get("topic", "a sports video")
        return _SYSTEM, (f"Draft SEO keywords and platform hashtag sets (YouTube, TikTok, Instagram) "
                         f"for: {topic}. Keep hashtags relevant and policy-safe. Draft only.")


class PostingTimeStrategyDraft(DraftSkill):
    spec = SkillSpec(name="posting_time_strategy_draft",
                     purpose="Draft a posting-time/cadence strategy (advisory; never schedules/posts).",
                     risk_level=RISK_LOW, allowed_actions=["create_draft", "summarize"],
                     triggers=["posting time", "best time to post", "cadence", "posting schedule"])

    def build_prompt(self, payload):
        platform = payload.get("platform", "YouTube Shorts")
        return _SYSTEM, (f"Draft an advisory posting cadence + time-of-day strategy for {platform} for a "
                         "faceless sports channel. Note it is advisory only — the owner schedules. Draft only.")


# ---- Community department -------------------------------------------- #
class TemplateReplyDraft(DraftSkill):
    spec = SkillSpec(name="template_reply_draft",
                     purpose="Draft APPROVED-STYLE comment/DM reply templates (never sends).",
                     risk_level=RISK_LOW, allowed_actions=["create_draft", "summarize"],
                     triggers=["reply template", "comment reply", "dm template", "community reply"])

    def build_prompt(self, payload):
        scenario = payload.get("scenario", "a viewer asking where a clip is from")
        return _SYSTEM, (f"Draft 3 brand-safe, template-style replies for: {scenario}. No links, no "
                         "promises, no personal data. These are TEMPLATES for owner approval — never sent. Draft only.")


# ---- Commerce department --------------------------------------------- #
class MerchIdeaDraft(DraftSkill):
    spec = SkillSpec(name="merch_idea_draft",
                     purpose="Draft merch/product concept ideas (research only; never lists or sells).",
                     risk_level=RISK_MEDIUM, allowed_actions=["create_draft", "research_public_info", "summarize"],
                     triggers=["merch", "merchandise", "product idea", "store idea"])

    def build_prompt(self, payload):
        audience = payload.get("audience", "sports content viewers")
        return _SYSTEM, (f"Draft 5 merch/product concepts for: {audience}. For each note the angle and a "
                         "reminder that licensing/IP must be cleared. Do NOT create listings or sell. Draft only.")


# ---- Technology Scout ------------------------------------------------ #
class ToolEvaluationDraft(DraftSkill):
    spec = SkillSpec(name="tool_evaluation_draft",
                     purpose="Draft an evaluation of a tool/skill/provider (recommend only; never installs).",
                     risk_level=RISK_LOW, allowed_actions=["create_draft", "research_public_info", "summarize"],
                     triggers=["evaluate tool", "tool evaluation", "scout", "should we use"])

    def build_prompt(self, payload):
        tool = payload.get("tool", "a new open-source tool")
        return _SYSTEM, (f"Draft an evaluation of: {tool}. Cover cost (prefer free/open-source/local), "
                         "fit, risks, and a recommend/hold call. Note it must be owner-approved + Sentinel-audited "
                         "before any install. Draft only.")


# All new pack skills (in registration order).
ALL_PACK_SKILLS = [
    ThumbnailConceptDraft, TitleCardCopyDraft,
    SeoHashtagDraft, PostingTimeStrategyDraft,
    TemplateReplyDraft, MerchIdeaDraft, ToolEvaluationDraft,
]

# Department -> skill names (reusable; a skill may appear in multiple departments).
DEPARTMENT_PACKS = {
    "research": ["sports_topic_research_draft", "tool_evaluation_draft"],
    "content": ["video_idea_draft", "script_outline_draft", "title_card_copy_draft"],
    "video": ["script_outline_draft", "title_card_copy_draft"],
    "creative": ["thumbnail_concept_draft", "title_card_copy_draft"],
    "marketing": ["seo_hashtag_draft", "posting_time_strategy_draft"],
    "community": ["template_reply_draft"],
    "commerce": ["affiliate_product_research_draft", "merch_idea_draft"],
    "compliance": ["compliance_review_draft"],
    "analytics": ["daily_report_draft"],
    "tech_scout": ["tool_evaluation_draft"],
}

# Cross-reference to the original skills so packs can resolve every name.
_ORIGINAL = [SportsTopicResearchDraft, VideoIdeaDraft, ScriptOutlineDraft,
             AffiliateProductResearchDraft, ComplianceReviewDraft, DailyReportDraft]
