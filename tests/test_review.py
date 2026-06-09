"""Tests for the owner-review surface (drafts, approve-draft-only, reject, revise, logging)."""

import pytest

from agents.base import STATUS_READY_FOR_REVIEW, Task
from agents.compliance import Compliance
from agents.hermes import Hermes
from agents.openclaw import OpenClaw
from agents.sentinel import Sentinel
from core.llm_router import LLMRouter
from memory.manager import MemoryManager
from review.models import (
    STATUS_OWNER_APPROVED,
    STATUS_READY,
    STATUS_REJECTED,
    STATUS_REVISION,
    make_review_item,
)
from review.service import ReviewError, ReviewService
from review.store import ReviewStore
from skills.registry import default_registry


def build_review_org(tmp_path):
    memory = MemoryManager(store_dir=tmp_path / "mem")
    store = ReviewStore(base_dir=tmp_path / "review")
    llm = LLMRouter()  # mock mode
    shared = {"config": None, "memory": memory, "llm": llm}
    hermes = Hermes(review_store=store, **shared)
    hermes.register(OpenClaw(registry=default_registry(), **shared))
    hermes.register(Sentinel(**shared))
    hermes.register(Compliance(**shared))
    service = ReviewService(store, memory=memory, reviser=hermes)
    return hermes, service, store, memory


def test_draft_appears_in_owner_review_surface(tmp_path):
    hermes, service, _, _ = build_review_org(tmp_path)
    result = hermes.handle(Task(name="request", payload={"text": "draft a daily report"}))
    assert result.status == STATUS_READY_FOR_REVIEW
    review_id = result.data["review_id"]
    assert review_id
    item = service.get(review_id)
    assert item.status == STATUS_READY
    assert item.published is False
    assert item.skill == "daily_report_draft"
    assert any(i.id == review_id for i in service.list_pending())


def test_approve_draft_only_sets_owner_approved_not_published(tmp_path):
    _, service, store, _ = build_review_org(tmp_path)
    item = make_review_item("daily_report_draft", "draft body", 0, {"passed": True, "risk_score": 0})
    store.add(item)
    approved = service.approve(item.id)
    assert approved.status == STATUS_OWNER_APPROVED
    assert approved.published is False
    assert all(i.id != item.id for i in service.list_pending())  # left the pending queue


def test_no_publish_anywhere():
    item = make_review_item("x", "y", 0, {})
    assert not hasattr(item, "publish")
    assert not hasattr(ReviewService, "publish")
    assert item.published is False


def test_reject_archives_with_reason(tmp_path):
    _, service, store, _ = build_review_org(tmp_path)
    item = make_review_item("video_idea_draft", "draft body", 0, {})
    store.add(item)
    rejected = service.reject(item.id, reason="off-brand")
    assert rejected.status == STATUS_REJECTED
    assert any(h["action"] == "owner_rejected" and "off-brand" in h["notes"] for h in rejected.history)
    assert all(i.id != item.id for i in service.list_pending())
    assert any(i.id == item.id for i in store.list(include_archived=True, status=STATUS_REJECTED))


def test_reject_requires_reason(tmp_path):
    _, service, store, _ = build_review_org(tmp_path)
    item = make_review_item("video_idea_draft", "draft body", 0, {})
    store.add(item)
    with pytest.raises(ReviewError):
        service.reject(item.id, reason="  ")


def test_request_revision_creates_task_and_new_draft(tmp_path):
    hermes, service, _, _ = build_review_org(tmp_path)
    first = hermes.handle(Task(name="request", payload={"text": "draft a daily report"}))
    original_id = first.data["review_id"]
    out = service.request_revision(original_id, notes="make it shorter")
    assert out["item"].status == STATUS_REVISION
    assert out["task"].payload["revise_of"] == original_id
    assert out["result"] is not None
    new_id = out["result"].data["review_id"]
    assert new_id and new_id != original_id
    assert any(i.id == new_id for i in service.list_pending())


def test_all_actions_logged_to_events_and_audit(tmp_path):
    hermes, service, _, memory = build_review_org(tmp_path)
    r1 = hermes.handle(Task(name="request", payload={"text": "draft a daily report"}))
    r2 = hermes.handle(Task(name="request", payload={"text": "draft some video ideas about the finals"}))
    r3 = hermes.handle(Task(name="request", payload={"text": "draft a script outline for a highlight"}))

    service.approve(r1.data["review_id"])
    service.reject(r2.data["review_id"], reason="not a fit")
    service.request_revision(r3.data["review_id"], notes="tighten the hook")

    events = memory.read_events()
    assert "review_submitted" in events
    assert "review_owner_approved" in events
    assert "review_owner_rejected" in events
    assert "review_owner_revision_requested" in events

    # Structured audit log carries the required fields.
    audit = memory.read_audit()
    assert "draft_created" in audit
    assert "owner_approved" in audit
    assert "compliance_score" in audit
    assert "final_status" in audit
