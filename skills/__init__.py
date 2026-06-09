"""Sportsverse OS — skills package.

Draft-only skills executed by OpenClaw under Hermes. Every skill is whitelisted in a
registry and declares its risk level, allowed/prohibited actions, and approval
requirement. Skills may produce drafts and reports ONLY — they can never publish, post,
email externally, buy, upload, or modify production code (enforced by the registry,
OpenClaw, and Sentinel).
"""

from skills.base import DraftSkill, SkillResult, SkillSpec  # noqa: F401
from skills.registry import SkillRegistry, default_registry  # noqa: F401

__all__ = ["SkillSpec", "SkillResult", "DraftSkill", "SkillRegistry", "default_registry"]
