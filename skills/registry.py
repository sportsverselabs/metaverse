"""Whitelist-based skill registry.

Only skills explicitly registered here can ever run. Registration is gated:
``register()`` refuses any skill that is not draft-only or whose ``allowed_actions``
intersect ``core.policy.FORBIDDEN_ACTIONS``. This makes "draft skills cannot publish" a
structural guarantee, not just a convention.
"""

from __future__ import annotations

from typing import Optional

from core.logging_setup import get_logger
from core.policy import FORBIDDEN_ACTIONS
from skills.base import DraftSkill, SkillSpec

_log = get_logger("skills.registry")


class SkillRegistry:
    def __init__(self) -> None:
        self._skills: dict[str, DraftSkill] = {}

    def register(self, skill: DraftSkill) -> None:
        spec: SkillSpec = skill.spec
        if not spec.draft_only:
            raise ValueError(f"refusing to register non-draft skill '{spec.name}'")
        bad = set(spec.allowed_actions) & set(FORBIDDEN_ACTIONS)
        if bad:
            raise ValueError(f"skill '{spec.name}' allows forbidden actions: {sorted(bad)}")
        self._skills[spec.name] = skill
        _log.info("Whitelisted skill '%s' (risk=%s)", spec.name, spec.risk_level)

    def get(self, name: str) -> Optional[DraftSkill]:
        return self._skills.get(name)

    def has(self, name: str) -> bool:
        return name in self._skills

    def names(self) -> list[str]:
        return sorted(self._skills)

    def specs(self) -> list[SkillSpec]:
        return [s.spec for s in self._skills.values()]


def default_registry() -> SkillRegistry:
    """Registry preloaded with the initial draft-only skills + the department skill packs."""
    from skills.drafts import ALL_DRAFT_SKILLS
    from skills.packs import ALL_PACK_SKILLS

    reg = SkillRegistry()
    for skill_cls in [*ALL_DRAFT_SKILLS, *ALL_PACK_SKILLS]:
        reg.register(skill_cls())
    return reg
