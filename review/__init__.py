"""Sportsverse OS — owner-review surface with gated automation.

The human approval gate. Drafts that finish the Hermes pipeline are queued here as
:class:`~review.models.ReviewItem` objects (status ``ready_for_owner_review``). The owner
can approve the draft, request a revision, reject it, or approve it for scheduled publishing.

Critically, NOTHING here publishes:
- approve            -> ``owner_approved``                  (draft ok; not scheduled)
- approve-schedule   -> ``approved_for_scheduled_publish``  (cleared for a FUTURE scheduler)
Both leave ``published = False``. Actual publishing is a future, separately-approved phase.
"""

from review.automation import GateReport, GateResult, evaluate_scheduling_gates, preflight  # noqa: F401
from review.models import (  # noqa: F401
    STATUS_COMPLIANCE_REVIEWED,
    STATUS_DRAFT_CREATED,
    STATUS_OWNER_APPROVED,
    STATUS_PUBLISHED,
    STATUS_READY,
    STATUS_REJECTED,
    STATUS_REVISION,
    STATUS_SCHEDULED,
    ReviewItem,
    make_review_item,
)
from review.service import ReviewError, ReviewService  # noqa: F401
from review.store import ReviewStore  # noqa: F401

__all__ = [
    "ReviewItem",
    "ReviewStore",
    "ReviewService",
    "ReviewError",
    "make_review_item",
    "evaluate_scheduling_gates",
    "preflight",
    "GateReport",
    "GateResult",
    "STATUS_DRAFT_CREATED",
    "STATUS_COMPLIANCE_REVIEWED",
    "STATUS_READY",
    "STATUS_REVISION",
    "STATUS_REJECTED",
    "STATUS_OWNER_APPROVED",
    "STATUS_SCHEDULED",
    "STATUS_PUBLISHED",
]
