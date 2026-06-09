"""Sentinel — integrity / security / drift monitor.

Sentinel reviews skill permissions against the constitution before a skill runs, blocks
high-risk skills by default, and logs warnings to memory. It also exposes the original
security/drift scan stubs. It never fixes things silently — it reports up to Hermes.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from agents.base import AgentResult, BaseAgent, STATUS_BLOCKED, STATUS_OK, Task
from core.policy import BLOCKED_RISK_LEVELS, FORBIDDEN_ACTIONS


@dataclass
class SentinelVerdict:
    allowed: bool
    reasons: list[str] = field(default_factory=list)   # why it was blocked (if blocked)
    warnings: list[str] = field(default_factory=list)  # non-blocking concerns


class Sentinel(BaseAgent):
    name = "sentinel"
    role = "Integrity / Security / Drift Monitor"
    reports_to = "hermes"

    # ------------------------------------------------------------------ #
    # Skill-permission review (the Phase 2A addition)
    # ------------------------------------------------------------------ #
    def review_skill(self, spec) -> SentinelVerdict:
        """Validate a skill spec against the constitution. Blocks high-risk by default."""
        reasons: list[str] = []
        warnings: list[str] = []

        if spec.risk_level in BLOCKED_RISK_LEVELS:
            reasons.append(f"risk_level '{spec.risk_level}' is blocked by default")
        if not spec.draft_only:
            reasons.append("skill is not draft-only")
        forbidden = set(spec.allowed_actions) & set(FORBIDDEN_ACTIONS)
        if forbidden:
            reasons.append(f"skill allows forbidden actions: {sorted(forbidden)}")

        if not spec.requires_human_approval:
            warnings.append("skill does not require human approval")
        missing = set(FORBIDDEN_ACTIONS) - set(spec.prohibited_actions)
        if missing:
            warnings.append(f"prohibited list does not explicitly cover: {sorted(missing)}")

        verdict = SentinelVerdict(allowed=not reasons, reasons=reasons, warnings=warnings)
        self._log_to_memory(spec.name, verdict)
        return verdict

    def _log_to_memory(self, skill_name: str, verdict: SentinelVerdict) -> None:
        """Record blocks/warnings to memory so there is an audit trail."""
        if self.memory is None or not hasattr(self.memory, "log_event"):
            return
        try:
            for reason in verdict.reasons:
                self.memory.log_event("sentinel_block", f"{skill_name}: {reason}")
            for warning in verdict.warnings:
                self.memory.log_event("sentinel_warning", f"{skill_name}: {warning}")
        except Exception:  # logging must never break the pipeline
            self.log.debug("Sentinel memory logging failed", exc_info=True)

    # ------------------------------------------------------------------ #
    # Original scan stubs (unchanged)
    # ------------------------------------------------------------------ #
    def security_scan(self) -> dict:
        self.log.debug("security_scan: skeleton (no checks run)")
        return {"status": "not_implemented", "issues": []}

    def check_drift(self) -> dict:
        self.log.debug("check_drift: skeleton (no checks run)")
        return {"status": "not_implemented", "drift": []}

    def handle(self, task: Task) -> AgentResult:
        if task.name == "review_skill":
            spec = task.payload.get("spec")
            if spec is None:
                return AgentResult(self.name, STATUS_BLOCKED, "no spec provided to review")
            verdict = self.review_skill(spec)
            status = STATUS_OK if verdict.allowed else STATUS_BLOCKED
            return AgentResult(self.name, status, "skill reviewed",
                               data={"allowed": verdict.allowed, "reasons": verdict.reasons, "warnings": verdict.warnings})
        if task.name in {"security_scan", "scan"}:
            return AgentResult(self.name, STATUS_OK, "security scan (skeleton)", data=self.security_scan())
        if task.name in {"check_drift", "drift"}:
            return AgentResult(self.name, STATUS_OK, "drift check (skeleton)", data=self.check_drift())
        return self.not_implemented(f"sentinel task '{task.name}'")
