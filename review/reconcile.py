"""Reconcile gated actions (approval queue) against draft/review records.

A gated action (e.g. ``publish_content``) should trace back to a real draft in the review store.
When it doesn't — e.g. a ``publish_content`` action spawned by a research task that never produced a
reviewable draft — it is **orphaned**: it clutters Approvals with nothing to act on. This module
detects orphans and can safely reconcile them (reject, which is reversible — the file is retained).
Nothing here publishes.
"""

from __future__ import annotations

from typing import Optional


def _linked(req, review_items) -> bool:
    details = getattr(req, "details", None) or {}
    rid = details.get("review_id")
    if rid and any(getattr(it, "id", None) == rid for it in review_items):
        return True
    task_id = getattr(req, "task_id", "") or ""
    if task_id and any(task_id in (getattr(it, "source_text", "") or "") for it in review_items):
        return True
    return False


def audit_actions(approval_queue=None, review_store=None) -> list[dict]:
    """Return one dict per PENDING gated action: {id, action, task_id, orphaned, reason}."""
    from approval.approval_queue import ApprovalQueue
    from review.store import ReviewStore
    aq = approval_queue or ApprovalQueue()
    rs = review_store or ReviewStore()
    try:
        items = rs.list(include_archived=True)
    except Exception:
        items = []
    out = []
    for req in aq.list(status="pending"):
        linked = _linked(req, items)
        out.append({"id": req.id, "action": req.action, "task_id": getattr(req, "task_id", ""),
                    "orphaned": not linked,
                    "reason": "" if linked else "no backing draft/review record"})
    return out


def find_orphaned(approval_queue=None, review_store=None) -> list[dict]:
    return [a for a in audit_actions(approval_queue, review_store) if a["orphaned"]]


def reconcile(apply: bool = False, approval_queue=None, review_store=None) -> dict:
    """Report orphaned gated actions; if ``apply``, reject them (reversible — records are kept)."""
    from approval.approval_queue import ApprovalQueue
    aq = approval_queue or ApprovalQueue()
    orphans = find_orphaned(aq, review_store)
    rejected = []
    if apply:
        for o in orphans:
            try:
                aq.reject(o["id"], reason="orphaned gated action (no backing draft) — auto-reconciled")
                rejected.append(o["id"])
            except Exception:
                pass
    return {"orphaned": orphans, "rejected": rejected, "applied": apply}
