"""Scheduled-slot model. A slot says WHEN an approved item should go out — not that it did.

``published`` exists only to assert the invariant (always False here). The scheduler never
publishes; a future Phase 4 publisher is the only place that could change.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from typing import Any

SLOT_PROPOSED = "proposed"
SLOT_CONFIRMED = "confirmed"
SLOT_CANCELLED = "cancelled"
ALL_SLOT_STATUSES = frozenset({SLOT_PROPOSED, SLOT_CONFIRMED, SLOT_CANCELLED})


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def new_slot_id() -> str:
    return f"sch-{date.today().isoformat()}-{uuid.uuid4().hex[:8]}"


@dataclass
class ScheduledSlot:
    id: str
    review_id: str                 # the approved review item this slot is for
    skill: str
    scheduled_for: str             # ISO datetime string (when it *would* go out)
    status: str = SLOT_PROPOSED
    created: str = ""
    updated: str = ""
    published: bool = False        # INVARIANT: never True in this phase
    history: list[dict] = field(default_factory=list)

    def add_history(self, action: str, *, by: str = "owner", notes: str = "") -> None:
        self.history.append({"ts": _now(), "action": action, "by": by, "notes": notes})
        self.updated = _now()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ScheduledSlot":
        return cls(**data)


def make_slot(review_id: str, skill: str, scheduled_for: str) -> ScheduledSlot:
    now = _now()
    slot = ScheduledSlot(
        id=new_slot_id(),
        review_id=review_id,
        skill=skill,
        scheduled_for=scheduled_for,
        status=SLOT_PROPOSED,
        created=now,
        updated=now,
        published=False,
    )
    slot.add_history("proposed", by="scheduler", notes=f"proposed time {scheduled_for} (NOT published)")
    return slot
