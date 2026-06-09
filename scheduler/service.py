"""Scheduler service — propose / confirm / cancel times for approved items. NEVER posts.

Reads items the owner cleared as ``approved_for_scheduled_publish`` from the review store and
proposes times. The owner can confirm or cancel a proposed time. A confirmed slot is still NOT
published — it is a plan for a future, separately-approved publisher (Phase 4). Every action is
written to the structured audit log.
"""

from __future__ import annotations

from typing import Optional

from core.logging_setup import get_logger
from review.models import STATUS_SCHEDULED  # "approved_for_scheduled_publish"
from scheduler.models import (
    SLOT_CANCELLED,
    SLOT_CONFIRMED,
    SLOT_PROPOSED,
    ScheduledSlot,
    make_slot,
)
from scheduler.planner import propose_times


class SchedulerError(Exception):
    """Raised for invalid scheduler operations (missing slot, bad transition, ...)."""


class SchedulerService:
    def __init__(self, store, review_store, memory=None, *,
                 post_hour: int = 17, spacing_days: int = 1, logger=None) -> None:
        self.store = store
        self.review_store = review_store
        self.memory = memory
        self.post_hour = post_hour
        self.spacing_days = spacing_days
        self.log = logger or get_logger("scheduler.service")

    # ------------------------------------------------------------------ #
    def propose_schedule(self) -> list[ScheduledSlot]:
        """Create proposed slots for approved items that don't already have one."""
        approved = self.review_store.list(status=STATUS_SCHEDULED)
        already = self.store.review_ids_with_slots()
        pending = [item for item in approved if item.id not in already]
        if not pending:
            self.log.info("No new approved items to schedule.")
            return []

        times = propose_times(len(pending), post_hour=self.post_hour, spacing_days=self.spacing_days)
        slots: list[ScheduledSlot] = []
        for item, when in zip(pending, times):
            slot = make_slot(item.id, item.skill, when.isoformat(timespec="minutes"))
            self.store.add(slot)
            self._audit(slot, "schedule_proposed", final_status=SLOT_PROPOSED)
            slots.append(slot)
        return slots

    def list(self, *, status: Optional[str] = None) -> list[ScheduledSlot]:
        return self.store.list(status=status)

    def get(self, slot_id: str) -> ScheduledSlot:
        slot = self.store.get(slot_id)
        if slot is None:
            raise SchedulerError(f"slot '{slot_id}' not found")
        return slot

    def confirm(self, slot_id: str, *, by: str = "owner") -> ScheduledSlot:
        """Owner confirms a proposed time. Still NOT published."""
        slot = self.get(slot_id)
        if slot.status == SLOT_CANCELLED:
            raise SchedulerError("cannot confirm a cancelled slot")
        slot.status = SLOT_CONFIRMED
        slot.published = False  # invariant
        slot.add_history("confirmed", by=by, notes="time confirmed (NOT published)")
        self.store.update(slot)
        self._audit(slot, "schedule_confirmed", owner_decision="confirm", final_status=SLOT_CONFIRMED)
        self.log.info("Confirmed slot %s for %s. Nothing published.", slot.id, slot.scheduled_for)
        return slot

    def cancel(self, slot_id: str, *, reason: str = "", by: str = "owner") -> ScheduledSlot:
        slot = self.get(slot_id)
        slot.status = SLOT_CANCELLED
        slot.add_history("cancelled", by=by, notes=reason or "(no reason given)")
        self.store.update(slot)
        self._audit(slot, "schedule_cancelled", owner_decision=reason, final_status=SLOT_CANCELLED)
        return slot

    # ------------------------------------------------------------------ #
    def _audit(self, slot: ScheduledSlot, action: str, *, owner_decision: str = "", final_status: str = "") -> None:
        if self.memory is not None and hasattr(self.memory, "log_audit"):
            try:
                self.memory.log_audit(draft_id=slot.review_id, action=action, agent="scheduler",
                                      owner_decision=owner_decision, compliance_score=None,
                                      final_status=final_status or slot.status)
            except Exception:
                self.log.debug("audit log failed", exc_info=True)
        if self.memory is not None and hasattr(self.memory, "log_event"):
            try:
                self.memory.log_event(action, f"slot {slot.id} (review {slot.review_id}) -> {slot.status} @ {slot.scheduled_for}")
            except Exception:
                self.log.debug("event log failed", exc_info=True)
