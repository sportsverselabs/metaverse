"""Sportsverse OS — scheduler (Phase 3). Assigns times; NEVER posts.

Takes review items that the owner cleared as ``approved_for_scheduled_publish`` and proposes
times for them, producing a schedule the owner confirms. It does NOT contain any posting or
platform-API code: a "confirmed" slot only records *when* an approved item should go out, for a
FUTURE publisher module (Phase 4) that requires its own separate owner approval.

Slot statuses: ``proposed`` -> ``confirmed`` / ``cancelled``. There is no "published" here.
"""

from scheduler.models import (  # noqa: F401
    SLOT_CANCELLED,
    SLOT_CONFIRMED,
    SLOT_PROPOSED,
    ScheduledSlot,
    make_slot,
)
from scheduler.planner import propose_times  # noqa: F401
from scheduler.service import SchedulerError, SchedulerService  # noqa: F401
from scheduler.store import SchedulerStore  # noqa: F401

__all__ = [
    "ScheduledSlot",
    "make_slot",
    "SLOT_PROPOSED",
    "SLOT_CONFIRMED",
    "SLOT_CANCELLED",
    "propose_times",
    "SchedulerStore",
    "SchedulerService",
    "SchedulerError",
]
