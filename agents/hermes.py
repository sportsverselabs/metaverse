"""Hermes — CEO / orchestrator agent.

Hermes receives a natural-language task, classifies it to a whitelisted draft skill,
has Sentinel review the skill's permissions, delegates execution to OpenClaw, runs the
resulting draft through Compliance, logs every step to memory, and returns a result
marked ``ready_for_owner_review`` (never published).

Pipeline:
    NL task -> classify -> Sentinel.review_skill -> OpenClaw.handle (draft)
            -> Compliance.review_draft -> memory log -> READY FOR OWNER REVIEW

Hermes never executes skills itself and never publishes. Anything it can't route is
escalated to the owner.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

from agents.base import (
    AgentResult,
    BaseAgent,
    STATUS_BLOCKED,
    STATUS_ESCALATED,
    STATUS_READY_FOR_REVIEW,
    Task,
)
from core import paths


class Hermes(BaseAgent):
    name = "hermes"
    role = "CEO / Orchestrator"
    reports_to = "owner"

    def __init__(self, review_store=None, **kwargs) -> None:
        super().__init__(**kwargs)
        self._registry: dict[str, BaseAgent] = {}
        # Optional owner-review queue; if present, completed drafts are submitted to it.
        self.review_store = review_store

    # ------------------------------------------------------------------ #
    # Sub-agent registry
    # ------------------------------------------------------------------ #
    def register(self, agent: BaseAgent) -> None:
        if agent.reports_to is None:
            agent.reports_to = self.name
        self._registry[agent.name] = agent
        self.log.info("Registered agent '%s' (%s)", agent.name, agent.role)

    @property
    def agents(self) -> dict[str, BaseAgent]:
        return dict(self._registry)

    def get(self, name: str) -> Optional[BaseAgent]:
        return self._registry.get(name)

    # ------------------------------------------------------------------ #
    # Classification (rule-based, deterministic)
    # ------------------------------------------------------------------ #
    def classify(self, text: str) -> Optional[str]:
        """Map a natural-language request to a whitelisted skill name via triggers.

        Picks the skill whose longest matching trigger appears in the text (most specific
        wins). Returns None if nothing matches.
        """
        openclaw = self.get("openclaw")
        if openclaw is None or not hasattr(openclaw, "registry"):
            return None
        text_l = (text or "").lower()
        best_name: Optional[str] = None
        best_len = -1
        for spec in openclaw.registry.specs():
            for trigger in spec.triggers:
                if trigger in text_l and len(trigger) > best_len:
                    best_name, best_len = spec.name, len(trigger)
        return best_name

    # ------------------------------------------------------------------ #
    # Phase 4: Hermes as the multi-agent router (Executive Officer)
    # ------------------------------------------------------------------ #
    # Hermes is the final decision-maker. No sub-agent may publish, spend, message, install,
    # or change production systems without a gated approval — Hermes routes those to the gate.
    TASK_ROUTES = {
        "research": "research_agent",
        "content": "content_agent",
        "coding": "coding_agent",
        "reasoning": "nemotron_reasoning_agent",
        "compliance": "compliance_agent",
        "skill": "openclaw_skill_agent",
    }

    def route_task(self, task_type: str, *, complexity: str = "normal", risk: str = "low") -> str:
        """Map a task type to the worker node. Hermes owns this decision."""
        return self.TASK_ROUTES.get(task_type, "research_agent")

    def decide(self, state) -> object:
        """Set the route on the orchestration state and flag any gated actions for approval.

        Hermes does not execute anything — it decides where the task goes and whether it must
        pass a human-approval gate before any production action.
        """
        state.route = self.route_task(state.task_type, complexity=state.complexity, risk=state.risk)
        if getattr(state, "gated_actions", None):
            state.approval_kind = state.approval_kind or "action"
            for action in state.gated_actions:
                state.approval_reasons.append(f"gated action requires approval: {action}")
        self.log.info("Hermes routed '%s' -> %s (gated=%s)", state.task_type, state.route,
                      getattr(state, "gated_actions", []))
        return state

    def review_journal(self, limit: int = 20) -> list[dict]:
        """Read the most recent agent-journal entries so Hermes can review prior decisions."""
        path = paths.AGENT_JOURNAL
        if not path.exists():
            return []
        entries: list[dict] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return entries[-limit:]

    # ------------------------------------------------------------------ #
    # Delegation helper
    # ------------------------------------------------------------------ #
    def delegate(self, agent_name: str, task: Task) -> AgentResult:
        agent = self._registry.get(agent_name)
        if agent is None:
            return self.escalate(task, f"no agent named '{agent_name}' is registered")
        self.log.info("Delegating '%s' -> %s", task.name, agent_name)
        return agent.handle(task)

    # ------------------------------------------------------------------ #
    # Orchestration
    # ------------------------------------------------------------------ #
    def handle(self, task: Task) -> AgentResult:
        payload = task.payload or {}
        text = payload.get("text") or task.name
        self._log("task_received", f"from {task.requested_by}: {text[:140]}")

        openclaw = self.get("openclaw")
        sentinel = self.get("sentinel")
        compliance = self.get("compliance")

        if openclaw is None:
            return self.escalate(task, "no OpenClaw registered to execute skills")

        # 1) Classify the request to a whitelisted draft skill.
        skill_name = self.classify(text)
        if not skill_name:
            self._log("no_skill", f"no matching draft skill for: {text[:140]}")
            return AgentResult(self.name, STATUS_ESCALATED,
                               "no matching draft skill; escalating to owner", data={"text": text})

        spec = openclaw.registry.get(skill_name).spec

        # 2) Sentinel reviews the skill's permissions FIRST.
        if sentinel is not None and hasattr(sentinel, "review_skill"):
            verdict = sentinel.review_skill(spec)
            self._log("sentinel_review", f"{skill_name}: allowed={verdict.allowed} reasons={verdict.reasons}")
            if not verdict.allowed:
                return AgentResult(self.name, STATUS_BLOCKED,
                                   f"Sentinel blocked '{skill_name}': {verdict.reasons}",
                                   data={"skill": skill_name, "reasons": verdict.reasons})

        # 3) Delegate execution to OpenClaw (draft only).
        exec_result = self.delegate("openclaw", Task(name=skill_name, payload=payload, requested_by="hermes"))
        if exec_result.status == STATUS_BLOCKED:
            self._log("execution_blocked", f"{skill_name}: {exec_result.detail}")
            return AgentResult(self.name, STATUS_BLOCKED, exec_result.detail, data=exec_result.data)
        draft = exec_result.data.get("content", "")

        # 4) Compliance MUST run before anything is marked ready for owner review.
        if compliance is None or not hasattr(compliance, "review_draft"):
            self._log("compliance_missing", "cannot clear draft: no Compliance agent")
            return self.escalate(task, "Compliance unavailable; cannot clear draft for owner review")
        comp = compliance.review_draft(draft, platform=payload.get("platform"))
        self._log("compliance_review", f"{skill_name}: risk={comp.risk_score} verdict={comp.verdict}")

        # 5) Persist the draft + decision to memory.
        self._remember_draft(skill_name, draft, comp)

        # 6) Submit to the owner-review queue (if wired). This is what the owner sees.
        review_id = self._submit_for_review(skill_name, draft, comp, source_text=text)

        self._log("decision", f"{skill_name}: ready_for_owner_review risk={comp.risk_score} review_id={review_id}")

        return AgentResult(
            self.name,
            STATUS_READY_FOR_REVIEW,
            detail=(f"Draft from '{skill_name}' ready for owner review "
                    f"(risk {comp.risk_score}/100; human approval required; nothing published)."),
            data={
                "skill": skill_name,
                "draft": draft,
                "review_id": review_id,
                "is_mock": exec_result.data.get("is_mock"),
                "risk_score": comp.risk_score,
                "compliance": {"verdict": comp.verdict, "notes": comp.notes, "checks": comp.checks},
                "requires_human_approval": True,
                "published": False,
            },
        )

    # ------------------------------------------------------------------ #
    # Memory helpers (best-effort; never break the pipeline)
    # ------------------------------------------------------------------ #
    def _log(self, kind: str, summary: str) -> None:
        if self.memory is not None and hasattr(self.memory, "log_event"):
            try:
                self.memory.log_event(kind, summary)
            except Exception:
                self.log.debug("memory.log_event failed", exc_info=True)

    def _submit_for_review(self, skill: str, content: str, comp, *, source_text: str = ""):
        """Queue the finished draft into the owner-review surface. Returns the review id (or None)."""
        if self.review_store is None:
            return None
        try:
            from review.models import make_review_item  # local import avoids any import cycle

            item = make_review_item(
                skill,
                content,
                comp.risk_score,
                {
                    "verdict": comp.verdict,
                    "notes": comp.notes,
                    "risk_score": comp.risk_score,
                    "passed": bool(getattr(comp, "passed", False)),
                },
                source_text=source_text,
                sentinel_passed=True,          # we only reach here after Sentinel cleared the skill
                compliance_passed=bool(getattr(comp, "passed", False)),
            )
            self.review_store.add(item)
            self._log("review_submitted", f"{skill}: {item.id} ready_for_owner_review")
            # Structured audit trail for the pipeline stages.
            self._audit(item.id, "draft_created", agent="openclaw", final_status="draft_created")
            self._audit(item.id, "compliance_reviewed", agent="compliance",
                        compliance_score=comp.risk_score, final_status="compliance_reviewed")
            self._audit(item.id, "ready_for_owner_review", agent="hermes",
                        compliance_score=comp.risk_score, final_status="ready_for_owner_review")
            return item.id
        except Exception:
            self.log.debug("review submission failed", exc_info=True)
            return None

    def _audit(self, draft_id, action, *, agent="", owner_decision="", compliance_score=None, final_status=""):
        if self.memory is not None and hasattr(self.memory, "log_audit"):
            try:
                self.memory.log_audit(draft_id=draft_id, action=action, agent=agent,
                                      owner_decision=owner_decision, compliance_score=compliance_score,
                                      final_status=final_status)
            except Exception:
                self.log.debug("audit log failed", exc_info=True)

    def _remember_draft(self, skill: str, content: str, comp) -> None:
        if self.memory is None or not hasattr(self.memory, "remember"):
            return
        try:
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            self.memory.remember(
                f"draft {skill} {stamp}",
                content,
                mem_type="project",
                description=f"draft from {skill} (risk {comp.risk_score}; awaiting owner review)",
            )
        except Exception:
            self.log.debug("memory.remember failed", exc_info=True)
