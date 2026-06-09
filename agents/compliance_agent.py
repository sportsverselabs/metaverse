"""Compliance agent (Phase 4 node wrapper).

Reuses the Phase 2 :class:`~agents.compliance.Compliance` risk scorer and writes the result onto
the orchestration state. Always runs after a worker so every output is compliance-reviewed before
any approval/execution step. Never auto-approves; a human always decides.
"""

from __future__ import annotations

from typing import Any

from agents.compliance import Compliance
from core.logging_setup import get_logger


class ComplianceAgent:
    name = "compliance_agent"

    def __init__(self, logger=None) -> None:
        self.log = logger or get_logger("agent.compliance_agent")
        self._compliance = Compliance(logger=self.log)

    def run(self, state: Any) -> Any:
        content = state.output or state.user_request
        platform = state.task_meta.get("platform") if isinstance(state.task_meta, dict) else None
        result = self._compliance.review_draft(content, platform=platform)
        state.compliance = {
            "verdict": result.verdict,
            "risk_score": result.risk_score,
            "passed": result.passed,
            "notes": result.notes,
        }
        # If this task IS a compliance task and produced no draft, surface the assessment as output.
        if not state.output and state.route == "compliance_agent":
            state.output = (f"Compliance assessment (risk {result.risk_score}/100, {result.verdict}). "
                            f"Notes: {result.notes}")
        state.tools_used.append(self.name)
        if not result.passed:
            state.approval_reasons.append(f"compliance risk {result.risk_score}/100 above threshold")
        self.log.info("Compliance: risk=%d passed=%s", result.risk_score, result.passed)
        return state
