"""Shared state for the Hermes/LangGraph orchestration graph.

A single dataclass threaded through every node. Works as the state schema for LangGraph (when
installed) and for the built-in fallback runner. ``path`` records node visitation order, used by
state-transition tests.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from typing import Any


def _new_task_id() -> str:
    return f"task-{date.today().isoformat()}-{uuid.uuid4().hex[:8]}"


@dataclass
class OrchestrationState:
    user_request: str
    source: str = "cli"                     # chat | cli | voice
    task_id: str = field(default_factory=_new_task_id)
    created: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))

    # Classification (set by Jarvis)
    task_type: str = ""
    complexity: str = "normal"              # normal | complex
    risk: str = "low"                       # low | high
    gated_actions: list[str] = field(default_factory=list)
    requested_skill: str = ""
    task_meta: dict = field(default_factory=dict)

    # Routing (set by Hermes)
    route: str = ""

    # Model / cost (set by cost_router / worker)
    model_provider: str = ""
    model_name: str = ""
    est_tokens: int = 0
    est_cost: float = 0.0
    is_mock: bool = False

    # Worker output
    output: str = ""
    tools_used: list[str] = field(default_factory=list)
    security_warnings: list[str] = field(default_factory=list)

    # Compliance
    compliance: dict = field(default_factory=dict)

    # Approval
    needs_approval: bool = False
    approval_kind: str = ""                 # "cost" | "action"
    approval_reasons: list[str] = field(default_factory=list)
    approval_status: str = "not_required"   # not_required | pending | approved | rejected
    approval_id: str = ""
    review_id: str = ""                     # set if the draft was queued into the review surface

    # Control / reporting
    path: list[str] = field(default_factory=list)   # nodes visited, in order
    final_status: str = ""
    report: str = ""
    error: str = ""

    def visit(self, node: str) -> None:
        self.path.append(node)

    def to_journal_record(self) -> dict[str, Any]:
        """The structured row written to the agent journal."""
        return {
            "ts": datetime.now().isoformat(timespec="seconds"),
            "task_id": self.task_id,
            "user_request": self.user_request,
            "source": self.source,
            "selected_route": self.route,
            "task_type": self.task_type,
            "complexity": self.complexity,
            "risk": self.risk,
            "model_used": f"{self.model_provider}/{self.model_name}" if self.model_provider else "",
            "estimated_tokens": self.est_tokens,
            "estimated_cost_usd": self.est_cost,
            "is_mock": self.is_mock,
            "tools_used": list(self.tools_used),
            "compliance_score": self.compliance.get("risk_score") if self.compliance else None,
            "approval_status": self.approval_status,
            "review_id": self.review_id,
            "security_warnings": list(self.security_warnings),
            "path": list(self.path),
            "final_status": self.final_status,
            "output_preview": " ".join((self.output or "").split())[:280],
        }

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
