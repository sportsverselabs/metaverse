"""Dashboard agent — assembles the owner dashboard data from all the stores (read-only)."""

from __future__ import annotations

from datetime import date

from core import paths
from core.logging_setup import get_logger
from orchestration.journal import AgentJournal
from providers.model_router import CostTracker
from review.store import ReviewStore
from scheduler.store import SchedulerStore


class DashboardAgent:
    name = "dashboard_agent"

    def __init__(self, *, review_store=None, scheduler_store=None, approval_queue=None,
                 journal=None, cost_tracker=None, logger=None) -> None:
        self.log = logger or get_logger("agent.dashboard")
        self.review_store = review_store or ReviewStore()
        self.scheduler_store = scheduler_store or SchedulerStore()
        self.journal = journal or AgentJournal()
        self.cost_tracker = cost_tracker or CostTracker()
        if approval_queue is None:
            from approval.approval_queue import ApprovalQueue
            approval_queue = ApprovalQueue()
        self.approval_queue = approval_queue

    def assemble_data(self) -> dict:
        from review.models import STATUS_OWNER_APPROVED, STATUS_READY, STATUS_SCHEDULED

        pending_drafts = self.review_store.list(status=STATUS_READY)
        approved = self.review_store.list(status=STATUS_OWNER_APPROVED)
        scheduled = self.review_store.list(status=STATUS_SCHEDULED)
        slots = self.scheduler_store.list()
        journal_rows = self.journal.read(limit=25)
        pending_actions = self.approval_queue.list(status="pending")

        return {
            "generated": date.today().isoformat(),
            "business": "Sportsverse / SportsVersusNews",
            "system_status": "operational (local)",
            "cost": {"month_total_usd": round(self.cost_tracker.month_total(), 4)},
            "pending_approvals": {
                "content": [{"id": i.id, "skill": i.skill, "risk": i.risk_score} for i in pending_drafts],
                "actions": [{"id": r.id, "action": r.action} for r in pending_actions],
            },
            "draft_articles": [{"id": i.id, "preview": " ".join((i.content or "").split())[:100]}
                               for i in pending_drafts if "content" in i.skill or "draft" in i.skill],
            "approved_for_schedule": [{"id": i.id, "skill": i.skill} for i in scheduled],
            "content_calendar": [{"slot": s.id, "review": s.review_id, "when": s.scheduled_for, "status": s.status}
                                 for s in slots],
            "agent_activity": [{"ts": r.get("ts"), "task": r.get("task_id"), "route": r.get("selected_route"),
                                "model": r.get("model_used"), "status": r.get("final_status")}
                               for r in journal_rows],
            "owner_todo": self._todos(pending_drafts, pending_actions, slots),
        }

    @staticmethod
    def _todos(pending_drafts, pending_actions, slots) -> list:
        todo = []
        if pending_drafts:
            todo.append(f"Review {len(pending_drafts)} draft(s): python -m review list")
        if pending_actions:
            todo.append(f"Decide {len(pending_actions)} gated action(s): python -m approval list")
        proposed = [s for s in slots if s.status == "proposed"]
        if proposed:
            todo.append(f"Confirm {len(proposed)} proposed schedule slot(s): python -m scheduler list")
        if not todo:
            todo.append("Nothing pending — give Jarvis a command: python -m orchestration \"...\"")
        return todo
