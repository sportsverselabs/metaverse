"""Human-approval gates for production / spending actions.

Nothing in this system may publish, send, spend, install, or change production state without a
matching approval here. The orchestration creates approval requests; the owner approves/rejects
them (``python -m approval``). Approval is required for every action in :data:`GATED_ACTIONS`.
"""

from approval.approval_queue import (  # noqa: F401
    GATED_ACTIONS,
    ApprovalQueue,
    ApprovalRequest,
    detect_gated_actions,
)

__all__ = ["GATED_ACTIONS", "ApprovalQueue", "ApprovalRequest", "detect_gated_actions"]
