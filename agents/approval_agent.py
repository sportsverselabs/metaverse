"""Approval agent — the owner's single approval surface.

Unifies two queues:
- **content** (articles / videos / posts) held in the Phase 2 review store, and
- **actions** (publish / spend / install / VPS / payments) held in the Phase 4 approval queue.

Owner operations: approve, reject, request edit, upload an edited version, and a final
"Are you sure?" confirmation before an item is cleared for scheduling. NOTHING here publishes —
confirming only sets ``approved_for_scheduled_publish`` for the (future, gated) scheduler/publisher.
"""

from __future__ import annotations

from typing import Optional

from approval.approval_queue import ApprovalQueue
from core.logging_setup import get_logger
from review.service import ReviewError, ReviewService
from review.store import ReviewStore


class ApprovalAgent:
    name = "approval_agent"

    def __init__(self, review_service: Optional[ReviewService] = None,
                 approval_queue: Optional[ApprovalQueue] = None, memory=None, logger=None) -> None:
        self.log = logger or get_logger("agent.approval")
        self.review = review_service or ReviewService(ReviewStore(), memory=memory)
        self.actions = approval_queue or ApprovalQueue(memory=memory)

    # ------------------------------------------------------------------ #
    def pending(self) -> dict:
        """All items awaiting the owner: content drafts + gated actions."""
        return {
            "content": [self._content_summary(i) for i in self.review.list_pending()],
            "actions": [{"id": r.id, "action": r.action, "reason": r.reason} for r in self.actions.list(status="pending")],
        }

    @staticmethod
    def _content_summary(item) -> dict:
        return {"id": item.id, "skill": item.skill, "risk": item.risk_score,
                "status": item.status, "preview": " ".join((item.content or "").split())[:120]}

    # ----- content operations (delegate to the review service) --------- #
    def approve(self, content_id: str):
        return self.review.approve(content_id)

    def reject(self, content_id: str, reason: str):
        return self.review.reject(content_id, reason)

    def request_edit(self, content_id: str, notes: str):
        return self.review.request_edit(content_id, notes)

    def upload_edited_version(self, content_id: str, edited_content: str):
        return self.review.upload_edited_version(content_id, edited_content)

    def confirm_publish(self, content_id: str, *, are_you_sure: bool = False):
        """Final 'Are you sure?' gate. Clears the item for the (future, gated) scheduler — does NOT publish."""
        if not are_you_sure:
            raise ReviewError("final confirmation required: pass are_you_sure=True (\"Are you sure you want to publish?\")")
        item = self.review.approve_for_scheduled_publish(content_id)
        self.log.info("Content %s cleared for scheduled publishing (NOT published).", content_id)
        return item

    # ----- action operations (delegate to the approval queue) ---------- #
    def approve_action(self, action_id: str):
        return self.actions.approve(action_id)

    def reject_action(self, action_id: str, reason: str = ""):
        return self.actions.reject(action_id, reason)
