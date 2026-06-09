"""Skill base types.

A skill bundles a declarative :class:`SkillSpec` (what it is and what it may/ may not do)
with a :meth:`DraftSkill.run` that produces a draft via the LLM router. Drafts are text
only; nothing here can publish or take an external action.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from core.policy import FORBIDDEN_ACTIONS, RISK_LOW

# Skill result statuses
STATUS_DRAFT = "draft"
STATUS_SKILL_BLOCKED = "blocked"
STATUS_SKILL_ERROR = "error"


@dataclass
class SkillSpec:
    """Declarative description of a skill. Required by the registry."""

    name: str
    purpose: str
    risk_level: str = RISK_LOW
    allowed_actions: list[str] = field(default_factory=lambda: ["create_draft"])
    prohibited_actions: list[str] = field(default_factory=lambda: sorted(FORBIDDEN_ACTIONS))
    requires_human_approval: bool = True
    draft_only: bool = True
    triggers: list[str] = field(default_factory=list)


@dataclass
class SkillResult:
    skill: str
    status: str
    content: str = ""
    notes: str = ""
    is_mock: bool = False
    data: dict = field(default_factory=dict)


class DraftSkill:
    """Base class for draft-only skills.

    Subclasses set :attr:`spec` and implement :meth:`build_prompt`. They never need to
    touch a provider — they call the injected LLM router, which is mock by default.
    """

    spec: SkillSpec

    def build_prompt(self, payload: dict) -> tuple[str, str]:
        """Return ``(system_prompt, user_prompt)`` for this skill."""
        raise NotImplementedError

    def run(self, payload: Optional[dict] = None, *, llm=None, logger=None) -> SkillResult:
        payload = payload or {}
        system, user = self.build_prompt(payload)
        if llm is None:
            # Still safe: produce an empty draft rather than crashing.
            return SkillResult(self.spec.name, STATUS_DRAFT, content="[no LLM router provided]", is_mock=True)
        resp = llm.complete(user, task_type="research", system=system)
        header = f"# DRAFT - {self.spec.name}\n# (draft only - requires human approval before any use)\n\n"
        return SkillResult(
            skill=self.spec.name,
            status=STATUS_DRAFT,
            content=header + resp.text,
            is_mock=getattr(resp, "is_mock", False),
            data={"provider": resp.provider, "model": resp.model},
        )
