"""OpenClaw — skill-execution layer (under Hermes).

OpenClaw executes concrete skills that Hermes assigns. It holds a whitelist
:class:`~skills.registry.SkillRegistry` and will only run skills that are registered AND
pass a defense-in-depth policy check (draft-only, no forbidden actions, not high-risk).
It never plans or sets strategy — that is Hermes's job — and it never publishes.
"""

from __future__ import annotations

from typing import Optional

from agents.base import AgentResult, BaseAgent, STATUS_BLOCKED, Task
from core.policy import FORBIDDEN_ACTIONS, RISK_HIGH
from skills.base import STATUS_DRAFT
from skills.registry import SkillRegistry


class OpenClaw(BaseAgent):
    name = "openclaw"
    role = "Skill-execution layer (under Hermes)"
    reports_to = "hermes"

    def __init__(self, registry: Optional[SkillRegistry] = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.registry = registry or SkillRegistry()

    @property
    def skills(self) -> list[str]:
        return self.registry.names()

    def handle(self, task: Task) -> AgentResult:
        """Execute the whitelisted skill named ``task.name``.

        Returns ``blocked`` if the skill is not whitelisted or fails the policy check.
        Otherwise returns a ``draft`` result whose ``data['content']`` holds the draft.
        """
        skill = self.registry.get(task.name)
        if skill is None:
            self.log.warning("Refused: skill '%s' is not whitelisted.", task.name)
            return AgentResult(self.name, STATUS_BLOCKED, f"skill '{task.name}' is not whitelisted")

        spec = skill.spec
        # Defense in depth — Sentinel is the primary gate, but OpenClaw double-checks.
        if not spec.draft_only:
            return AgentResult(self.name, STATUS_BLOCKED, f"skill '{spec.name}' is not draft-only")
        if spec.risk_level == RISK_HIGH:
            return AgentResult(self.name, STATUS_BLOCKED, f"skill '{spec.name}' is high-risk (blocked)")
        forbidden = set(spec.allowed_actions) & set(FORBIDDEN_ACTIONS)
        if forbidden:
            return AgentResult(self.name, STATUS_BLOCKED, f"skill '{spec.name}' allows forbidden actions: {sorted(forbidden)}")

        self.log.info("Executing draft skill '%s'", spec.name)
        result = skill.run(task.payload or {}, llm=self.llm, logger=self.log)
        return AgentResult(
            self.name,
            STATUS_DRAFT if result.status == STATUS_DRAFT else STATUS_BLOCKED,
            detail=f"draft produced by '{spec.name}'",
            data={
                "content": result.content,
                "skill": spec.name,
                "is_mock": result.is_mock,
                "risk_level": spec.risk_level,
                "requires_human_approval": spec.requires_human_approval,
                "published": False,
            },
        )
