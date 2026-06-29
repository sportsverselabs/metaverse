"""Review item model, status vocabulary, and gate state.

A :class:`ReviewItem` is a draft moving through the gated pipeline. It carries the draft
content, the compliance result, the per-gate state, a current status, and an append-only
history. ``published`` is present but is ALWAYS ``False`` in this phase — no approval ever
publishes. ``approved_for_scheduled_publish`` only clears an item for a FUTURE scheduler.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from typing import Any

# ---------------------------------------------------------------------------
# Status vocabulary (full lifecycle)
# ---------------------------------------------------------------------------
STATUS_DRAFT_CREATED = "draft_created"                  # Gate 1 cleared
STATUS_COMPLIANCE_REVIEWED = "compliance_reviewed"       # Gate 3 ran
STATUS_READY = "ready_for_owner_review"                  # waiting for the owner
STATUS_REVISION = "owner_revision_requested"             # owner asked for changes
STATUS_REJECTED = "owner_rejected"                       # owner rejected; archived w/ reason
STATUS_OWNER_APPROVED = "owner_approved"                 # owner approved the DRAFT only
STATUS_SCHEDULED = "approved_for_scheduled_publish"      # cleared for a FUTURE scheduler
STATUS_PUBLISHED = "published"                           # set only by explicit Phase 5 publisher

ALL_STATUSES = frozenset({
    STATUS_DRAFT_CREATED, STATUS_COMPLIANCE_REVIEWED, STATUS_READY, STATUS_REVISION,
    STATUS_REJECTED, STATUS_OWNER_APPROVED, STATUS_SCHEDULED, STATUS_PUBLISHED,
})
# Statuses considered "active" (live in the queue area, not archived).
ACTIVE_STATUSES = frozenset({
    STATUS_DRAFT_CREATED, STATUS_COMPLIANCE_REVIEWED, STATUS_READY,
    STATUS_REVISION, STATUS_OWNER_APPROVED, STATUS_SCHEDULED,
})

# ---------------------------------------------------------------------------
# Gate keys (the six gates that must pass before scheduled-publish approval)
# ---------------------------------------------------------------------------
GATE_DRAFT_CREATED = "gate1_draft_created"
GATE_SENTINEL = "gate2_sentinel_review"
GATE_COMPLIANCE = "gate3_compliance_review"
GATE_OWNER_APPROVAL = "gate4_owner_approval"
GATE_SCHEDULE_PERMISSION = "gate5_schedule_permission"
GATE_PREFLIGHT = "gate6_preflight"
GATE_ORDER = [
    GATE_DRAFT_CREATED, GATE_SENTINEL, GATE_COMPLIANCE,
    GATE_OWNER_APPROVAL, GATE_SCHEDULE_PERMISSION, GATE_PREFLIGHT,
]


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def new_id() -> str:
    """Short, unique review id, e.g. ``rv-2026-06-08-1a2b3c4d``."""
    return f"rv-{date.today().isoformat()}-{uuid.uuid4().hex[:8]}"


def _default_gates() -> dict[str, bool]:
    return {
        GATE_DRAFT_CREATED: False,
        GATE_SENTINEL: False,
        GATE_COMPLIANCE: False,
        GATE_OWNER_APPROVAL: False,
        GATE_SCHEDULE_PERMISSION: False,
        GATE_PREFLIGHT: False,
    }


@dataclass
class ReviewItem:
    id: str
    skill: str
    content: str
    risk_score: int = 0
    compliance: dict = field(default_factory=dict)   # {verdict, notes, risk_score, passed}
    status: str = STATUS_READY
    gates: dict = field(default_factory=_default_gates)
    created: str = ""
    updated: str = ""
    source_text: str = ""          # original NL request, used to build revision tasks
    published: bool = False        # True only after explicit Phase 5 publisher success
    published_at: str = ""
    published_platform: str = ""
    post_id: str = ""
    post_url: str = ""
    history: list[dict] = field(default_factory=list)

    def add_history(self, action: str, *, by: str = "owner", notes: str = "") -> None:
        self.history.append({"ts": _now(), "action": action, "by": by, "notes": notes})
        self.updated = _now()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ReviewItem":
        # Tolerate older records missing the gates field.
        data = dict(data)
        data.setdefault("gates", _default_gates())
        data.setdefault("published_at", "")
        data.setdefault("published_platform", "")
        data.setdefault("post_id", "")
        data.setdefault("post_url", "")
        return cls(**data)


def make_review_item(
    skill: str,
    content: str,
    risk_score: int,
    compliance: dict | None = None,
    *,
    source_text: str = "",
    sentinel_passed: bool = True,
    compliance_passed: bool = True,
) -> ReviewItem:
    """Build a review item in ``ready_for_owner_review`` with pipeline gates 1-3 recorded."""
    now = _now()
    gates = _default_gates()
    gates[GATE_DRAFT_CREATED] = True            # Gate 1: it exists
    gates[GATE_SENTINEL] = bool(sentinel_passed)  # Gate 2: Sentinel cleared the skill
    gates[GATE_COMPLIANCE] = bool(compliance_passed)  # Gate 3: compliance risk acceptable
    item = ReviewItem(
        id=new_id(),
        skill=skill,
        content=content,
        risk_score=int(risk_score or 0),
        compliance=compliance or {},
        status=STATUS_READY,
        gates=gates,
        created=now,
        updated=now,
        source_text=source_text,
        published=False,
    )
    item.add_history("draft_created", by="openclaw", notes="draft produced (Gate 1)")
    item.add_history("compliance_reviewed", by="compliance",
                     notes=f"Gate 3 risk={item.risk_score} passed={gates[GATE_COMPLIANCE]}")
    item.add_history("ready_for_owner_review", by="hermes", notes="queued for owner")
    return item
