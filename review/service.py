"""Review service — the owner's decision logic, with gated scheduling.

Owner actions:
- :meth:`approve`                     -> ``owner_approved``         (approve the DRAFT only)
- :meth:`request_revision`            -> ``owner_revision_requested`` + a revision Task
- :meth:`reject`                      -> ``owner_rejected``         (archived with a reason)
- :meth:`approve_for_scheduled_publish` -> ``approved_for_scheduled_publish`` IF all 6 gates pass

Nothing here publishes. ``approved_for_scheduled_publish`` only clears an item for a FUTURE
scheduler/publisher module that does not exist yet. Every action is written to the structured
audit log (timestamp, draft id, action, agent, owner decision, compliance score, final status).
"""

from __future__ import annotations

from typing import Optional

from agents.base import Task
from core.logging_setup import get_logger
from review.automation import evaluate_scheduling_gates
from review.models import (
    GATE_OWNER_APPROVAL,
    GATE_PREFLIGHT,
    GATE_SCHEDULE_PERMISSION,
    STATUS_OWNER_APPROVED,
    STATUS_REJECTED,
    STATUS_REVISION,
    STATUS_SCHEDULED,
    ReviewItem,
)


class ReviewError(Exception):
    """Raised for invalid review operations (missing item, missing reason, blocked gates...)."""


class ReviewService:
    def __init__(self, store, memory=None, reviser=None, logger=None) -> None:
        # ``reviser`` is a Hermes-like object with a ``handle(Task)`` method (optional).
        self.store = store
        self.memory = memory
        self.reviser = reviser
        self.log = logger or get_logger("review.service")

    # ------------------------------------------------------------------ #
    # Read
    # ------------------------------------------------------------------ #
    def list_pending(self) -> list[ReviewItem]:
        return self.store.list_pending()

    def list(self, *, status: Optional[str] = None, include_archived: bool = False) -> list[ReviewItem]:
        return self.store.list(status=status, include_archived=include_archived)

    def get(self, item_id: str) -> ReviewItem:
        item = self.store.get(item_id)
        if item is None:
            raise ReviewError(f"review item '{item_id}' not found")
        return item

    # ------------------------------------------------------------------ #
    # Owner action 1 — approve the draft only (NOT for scheduling)
    # ------------------------------------------------------------------ #
    def approve(self, item_id: str, *, by: str = "owner") -> ReviewItem:
        item = self.get(item_id)
        if item.status == STATUS_REJECTED:
            raise ReviewError("cannot approve a rejected item")
        item.status = STATUS_OWNER_APPROVED
        item.gates[GATE_OWNER_APPROVAL] = True
        item.published = False  # invariant
        item.add_history("owner_approved", by=by, notes="draft approved (NOT scheduled, NOT published)")
        self.store.update(item)
        self._audit(item, "owner_approved", owner_decision="approve_draft_only")
        self.log.info("Approved draft %s (owner_approved). Not scheduled, not published.", item.id)
        return item

    # ------------------------------------------------------------------ #
    # Owner action 2 — request a revision
    # ------------------------------------------------------------------ #
    def request_revision(self, item_id: str, notes: str, *, by: str = "owner") -> dict:
        if not notes or not notes.strip():
            raise ReviewError("revision notes are required")
        item = self.get(item_id)
        item.status = STATUS_REVISION
        item.add_history("owner_revision_requested", by=by, notes=notes.strip())
        self.store.update(item)
        self._audit(item, "owner_revision_requested", owner_decision=notes.strip())

        revision_text = (item.source_text or item.skill).strip()
        task = Task(
            name="request",
            payload={"text": revision_text, "revision_notes": notes.strip(), "revise_of": item.id},
            requested_by="owner-review",
        )
        result = None
        if self.reviser is not None and hasattr(self.reviser, "handle"):
            result = self.reviser.handle(task)  # produces a NEW draft -> new review item
            self._audit(item, "revision_task_run", owner_decision=f"new={result.data.get('review_id')}",
                        final_status=str(result.status))
        else:
            self._audit(item, "revision_task_created", owner_decision="(not auto-run)")
        return {"item": item, "task": task, "result": result}

    def request_edit(self, item_id: str, notes: str, *, by: str = "owner") -> dict:
        """Owner asks for edits — alias of request_revision (creates a revision task)."""
        return self.request_revision(item_id, notes, by=by)

    def upload_edited_version(self, item_id: str, edited_content: str, *, by: str = "owner") -> ReviewItem:
        """Owner uploads an externally-edited version. Becomes the draft; needs final confirm to schedule."""
        if not (edited_content or "").strip():
            raise ReviewError("edited content is empty")
        item = self.get(item_id)
        item.content = edited_content
        item.status = STATUS_OWNER_APPROVED
        item.add_history("owner_edited_upload", by=by,
                         notes="owner uploaded an edited version (draft approved; confirm to schedule)")
        self.store.update(item)
        self._audit(item, "owner_edited_upload", owner_decision="uploaded_edit")
        return item

    # ------------------------------------------------------------------ #
    # Owner action 3 — reject (archive with reason)
    # ------------------------------------------------------------------ #
    def reject(self, item_id: str, reason: str, *, by: str = "owner") -> ReviewItem:
        if not reason or not reason.strip():
            raise ReviewError("a non-empty reason is required to reject a draft")
        item = self.get(item_id)
        item.status = STATUS_REJECTED
        item.add_history("owner_rejected", by=by, notes=reason.strip())
        self.store.archive(item)
        self._audit(item, "owner_rejected", owner_decision=reason.strip())
        return item

    # ------------------------------------------------------------------ #
    # Owner action 4 — approve for scheduled publishing (gated; still NOT published)
    # ------------------------------------------------------------------ #
    def approve_for_scheduled_publish(self, item_id: str, *, by: str = "owner") -> ReviewItem:
        """Clear an item for a FUTURE scheduler IF all six gates pass. Never publishes."""
        item = self.get(item_id)
        if item.status == STATUS_REJECTED:
            raise ReviewError("cannot schedule a rejected item")

        report = evaluate_scheduling_gates(item, owner_authorizing=True)
        if not report.passed:
            item.add_history("schedule_blocked", by=by, notes=f"failing gates: {report.failing}")
            self.store.update(item)
            self._audit(item, "schedule_blocked", owner_decision="approve_for_scheduled_publish",
                        final_status=item.status)
            raise ReviewError(f"scheduling blocked - failing gates: {report.failing}")

        # All gates pass: record gates 4/5/6 and transition.
        item.gates[GATE_OWNER_APPROVAL] = True
        item.gates[GATE_SCHEDULE_PERMISSION] = True
        item.gates[GATE_PREFLIGHT] = True
        item.status = STATUS_SCHEDULED
        item.published = False  # INVARIANT: scheduling approval is NOT publishing
        item.add_history("approved_for_scheduled_publish", by=by,
                         notes="cleared for FUTURE scheduler only — NOT published")
        self.store.update(item)
        self._audit(item, "approved_for_scheduled_publish", owner_decision="approve_for_scheduled_publishing",
                    final_status=STATUS_SCHEDULED)
        self.log.info("Item %s approved_for_scheduled_publish (all 6 gates). NOTHING published.", item.id)
        return item

    # ------------------------------------------------------------------ #
    # Audit / logging
    # ------------------------------------------------------------------ #
    def _audit(self, item: ReviewItem, action: str, *, owner_decision: str = "", final_status: str = "") -> None:
        final = final_status or item.status
        score = item.compliance.get("risk_score") if isinstance(item.compliance, dict) else None
        if self.memory is not None and hasattr(self.memory, "log_audit"):
            try:
                self.memory.log_audit(draft_id=item.id, action=action, agent="owner-review",
                                      owner_decision=owner_decision, compliance_score=score, final_status=final)
            except Exception:
                self.log.debug("audit log failed", exc_info=True)
        if self.memory is not None and hasattr(self.memory, "log_event"):
            try:
                self.memory.log_event(f"review_{action}", f"{item.id} -> {final} ({owner_decision})".strip())
            except Exception:
                self.log.debug("event log failed", exc_info=True)
