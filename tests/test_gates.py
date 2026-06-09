"""Tests for the 6-gate scheduled-publish automation."""

import pytest

from memory.manager import MemoryManager
from review.automation import evaluate_scheduling_gates
from review.models import (
    GATE_OWNER_APPROVAL,
    GATE_PREFLIGHT,
    GATE_SCHEDULE_PERMISSION,
    STATUS_READY,
    STATUS_SCHEDULED,
    make_review_item,
)
from review.service import ReviewError, ReviewService
from review.store import ReviewStore


def _service(tmp_path):
    store = ReviewStore(base_dir=tmp_path / "review")
    memory = MemoryManager(store_dir=tmp_path / "mem")
    return ReviewService(store, memory=memory), store, memory


def _good_item(store):
    item = make_review_item(
        "daily_report_draft", "a clean internal report draft", 0,
        {"verdict": "needs_human_review", "risk_score": 0, "passed": True},
        compliance_passed=True, sentinel_passed=True,
    )
    store.add(item)
    return item


def test_owner_approval_required_before_scheduling(tmp_path):
    _, store, _ = _service(tmp_path)
    item = _good_item(store)
    # Without the owner authorizing, gates 4 and 5 fail -> cannot schedule.
    report = evaluate_scheduling_gates(item, owner_authorizing=False)
    assert report.passed is False
    assert GATE_OWNER_APPROVAL in report.failing
    assert GATE_SCHEDULE_PERMISSION in report.failing
    # With the owner authorizing (and gates 1-3, 6 fine), it passes.
    assert evaluate_scheduling_gates(item, owner_authorizing=True).passed is True


def test_scheduled_status_only_via_owner_action(tmp_path):
    svc, store, _ = _service(tmp_path)
    item = _good_item(store)
    assert item.status == STATUS_READY  # never auto-scheduled
    out = svc.approve_for_scheduled_publish(item.id)
    assert out.status == STATUS_SCHEDULED
    assert out.published is False
    assert out.gates[GATE_OWNER_APPROVAL] and out.gates[GATE_SCHEDULE_PERMISSION] and out.gates[GATE_PREFLIGHT]


def test_compliance_failure_blocks_scheduling(tmp_path):
    svc, store, _ = _service(tmp_path)
    bad = make_review_item(
        "affiliate_product_research_draft", "buy now, guaranteed results", 80,
        {"verdict": "needs_human_review", "risk_score": 80, "passed": False},
        compliance_passed=False,
    )
    store.add(bad)
    with pytest.raises(ReviewError):
        svc.approve_for_scheduled_publish(bad.id)
    assert store.get(bad.id).status != STATUS_SCHEDULED  # stays unscheduled


def test_scheduling_never_publishes(tmp_path):
    svc, store, _ = _service(tmp_path)
    item = _good_item(store)
    out = svc.approve_for_scheduled_publish(item.id)
    assert out.published is False
    assert all(not i.published for i in store.list(include_archived=True))


def test_schedule_blocked_is_audited(tmp_path):
    svc, store, memory = _service(tmp_path)
    bad = make_review_item("video_idea_draft", "guaranteed get rich", 90,
                           {"risk_score": 90, "passed": False}, compliance_passed=False)
    store.add(bad)
    with pytest.raises(ReviewError):
        svc.approve_for_scheduled_publish(bad.id)
    assert "schedule_blocked" in memory.read_audit()
