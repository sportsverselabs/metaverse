"""Jarvis — the command interface layer.

Jarvis receives user commands (chat / CLI / later voice), converts them into a STRUCTURED task
(task type, complexity, risk, any gated actions, optional skill), and reports status back in
plain English. Jarvis makes NO executive decisions — it hands the structured task to Hermes,
who routes it.
"""

from __future__ import annotations

import json
from typing import Any, Optional

from approval.approval_queue import detect_gated_actions
from core import paths
from core.logging_setup import get_logger

# Keyword -> task type (first match by longest keyword wins).
_TASK_KEYWORDS = {
    "research": ["research", "find trends", "trending", "analyze the market", "look up", "investigate", "competitor"],
    "content": ["draft", "write", "caption", "script", "content idea", "video idea", "post idea", "headline"],
    "coding": ["code", "fix the bug", "refactor", "implement", "function", "unit test", "debug"],
    "reasoning": ["architecture", "design the system", "strategy", "plan the", "business decision",
                  "long-context", "deep analysis", "evaluate options", "high-value"],
    "compliance": ["compliance", "is this allowed", "review for", "copyright", "fair use", "ftc"],
    "skill": ["run skill", "use skill", "openclaw", "skill:"],
}
_COMPLEX_HINTS = ("architecture", "strategy", "plan the", "business decision", "long-context",
                  "deep analysis", "evaluate options", "high-value", "multimodal", "design the system")


class Jarvis:
    name = "jarvis"

    def __init__(self, logger=None, context: Optional[dict] = None) -> None:
        self.log = logger or get_logger("agent.jarvis")
        self.context = context if context is not None else self._load_context()

    @staticmethod
    def _load_context() -> dict:
        try:
            p = paths.CONFIG_DIR / "project_context.json"
            if p.exists():
                return json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
        return {}

    # ------------------------------------------------------------------ #
    def parse(self, user_request: str, source: str = "cli") -> dict:
        """Turn a natural-language request into a structured task dict (no decisions made)."""
        text = (user_request or "").strip()
        low = text.lower()

        task_type, best_len = "research", -1
        for ttype, words in _TASK_KEYWORDS.items():
            for w in words:
                if w in low and len(w) > best_len:
                    task_type, best_len = ttype, len(w)

        complexity = "complex" if any(h in low for h in _COMPLEX_HINTS) else "normal"
        gated = detect_gated_actions(low)
        risk = "high" if gated else "low"

        skill = ""
        if "skill:" in low:
            skill = low.split("skill:", 1)[1].strip().split()[0]

        task = {
            "task_type": task_type,
            "complexity": complexity,
            "risk": risk,
            "gated_actions": gated,
            "requested_skill": skill,
            "source": source,
        }
        self.log.info("Jarvis parsed: type=%s complexity=%s risk=%s gated=%s",
                      task_type, complexity, risk, gated)
        return task

    # ------------------------------------------------------------------ #
    def report(self, state: Any) -> str:
        """Plain-English status back to the user."""
        lines = [f"Request: {state.user_request}"]
        lines.append(f"Routed to: {state.route or '(unrouted)'} via Hermes "
                     f"(task type: {state.task_type}, complexity: {state.complexity}).")
        if state.model_provider:
            lines.append(f"Model: {state.model_provider}/{state.model_name} "
                         f"(~{state.est_tokens} tokens, est ${state.est_cost:.4f}{', mock' if state.is_mock else ''}).")
        if state.compliance:
            lines.append(f"Compliance: risk {state.compliance.get('risk_score')}/100, "
                         f"verdict {state.compliance.get('verdict')}.")
        if state.security_warnings:
            lines.append("Security: " + "; ".join(state.security_warnings))
        if state.approval_status == "pending":
            lines.append(f"ACTION NEEDED: this requires your approval ({', '.join(state.approval_reasons) or 'gated action'}). "
                         f"Nothing was published, sent, or spent. Approve with: python -m approval list")
        if state.review_id:
            lines.append(f"Queued into the owner-review surface as {state.review_id} "
                         f"(review it with: python -m review show {state.review_id}).")
        if state.output:
            preview = " ".join(state.output.split())[:300]
            lines.append(f"Draft/output (not published): {preview}")
        lines.append(f"Final status: {state.final_status}.")
        report = "\n".join(lines)
        state.report = report
        return report
