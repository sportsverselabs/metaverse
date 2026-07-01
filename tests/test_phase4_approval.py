"""Approval queue + gated-action enforcement in the graph."""

import pytest

from approval.approval_queue import (
    APPROVAL_APPROVED,
    APPROVAL_PENDING,
    ApprovalQueue,
    detect_gated_actions,
)
from orchestration.routes import run_fallback
from orchestration.state import OrchestrationState
from tests._phase4_helpers import make_ctx


def test_detect_gated_actions():
    assert "publish_content" in detect_gated_actions("please publish this draft")
    assert "public_post" in detect_gated_actions("post on tiktok now")
    assert "send_email" in detect_gated_actions("send email to subscribers")
    assert detect_gated_actions("draft a YouTube short for owner review; do not publish") == []
    assert detect_gated_actions("create an Instagram caption draft, not a public post") == []
    assert detect_gated_actions("just summarize this article") == []


def test_approval_queue_request_approve_reject(tmp_path):
    q = ApprovalQueue(base_dir=tmp_path / "ap")
    req = q.request("publish_content", "owner wants to publish", task_id="t1")
    assert req.status == APPROVAL_PENDING
    assert q.list(status=APPROVAL_PENDING)
    approved = q.approve(req.id)
    assert approved.status == APPROVAL_APPROVED
    other = q.request("send_email", "newsletter", task_id="t2")
    rejected = q.reject(other.id, reason="not now")
    assert rejected.status == "rejected"


def test_gated_request_creates_pending_approval_and_does_not_execute(tmp_path):
    ctx = make_ctx(tmp_path)
    state = OrchestrationState(user_request="publish this update and post on instagram")
    run_fallback(state, ctx)
    assert state.approval_status == APPROVAL_PENDING
    assert state.approval_id
    assert state.final_status == "pending_approval"
    # An approval request exists in the queue.
    assert ctx.approval_queue.list(status=APPROVAL_PENDING)
    # Nothing was published/executed.
    assert state.final_status != "published"


def test_normal_task_needs_no_approval(tmp_path):
    ctx = make_ctx(tmp_path)
    state = OrchestrationState(user_request="research trending football stories")
    run_fallback(state, ctx)
    assert state.approval_status == "not_required"
    assert state.final_status == "completed_no_external_action"
