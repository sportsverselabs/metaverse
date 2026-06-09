"""Tests for the Phase 3 scheduler. It proposes/confirms times and NEVER publishes."""

from datetime import datetime

from memory.manager import MemoryManager
from review.models import STATUS_READY, STATUS_SCHEDULED, make_review_item
from review.store import ReviewStore
from scheduler.models import SLOT_CANCELLED, SLOT_CONFIRMED, SLOT_PROPOSED, ScheduledSlot
from scheduler.planner import propose_times
from scheduler.service import SchedulerError, SchedulerService
from scheduler.store import SchedulerStore


def _setup(tmp_path):
    review = ReviewStore(base_dir=tmp_path / "review")
    sched = SchedulerStore(base_dir=tmp_path / "schedule")
    memory = MemoryManager(store_dir=tmp_path / "mem")
    svc = SchedulerService(sched, review, memory=memory)
    return svc, review, sched, memory


def _approved_item(review_store, skill="daily_report_draft"):
    item = make_review_item(skill, "approved content", 0, {"passed": True, "risk_score": 0})
    item.status = STATUS_SCHEDULED  # owner approved it for scheduling
    review_store.add(item)
    return item


def test_planner_assigns_future_spaced_times():
    base = datetime(2026, 6, 8, 9, 0)
    times = propose_times(3, start=base, post_hour=17, spacing_days=1)
    assert [t.isoformat() for t in times] == [
        "2026-06-09T17:00:00", "2026-06-10T17:00:00", "2026-06-11T17:00:00",
    ]
    assert all(t > base for t in times)


def test_only_approved_for_scheduled_publish_items_are_scheduled(tmp_path):
    svc, review, _, _ = _setup(tmp_path)
    approved = _approved_item(review)
    # A plain ready item must NOT be scheduled.
    ready = make_review_item("video_idea_draft", "still pending", 0, {"passed": True})
    review.add(ready)
    assert ready.status == STATUS_READY

    slots = svc.propose_schedule()
    review_ids = {s.review_id for s in slots}
    assert approved.id in review_ids
    assert ready.id not in review_ids


def test_propose_is_idempotent(tmp_path):
    svc, review, _, _ = _setup(tmp_path)
    _approved_item(review)
    first = svc.propose_schedule()
    assert len(first) == 1
    second = svc.propose_schedule()  # nothing new to schedule
    assert second == []


def test_confirm_sets_confirmed_and_does_not_publish(tmp_path):
    svc, review, _, _ = _setup(tmp_path)
    _approved_item(review)
    slot = svc.propose_schedule()[0]
    assert slot.status == SLOT_PROPOSED
    confirmed = svc.confirm(slot.id)
    assert confirmed.status == SLOT_CONFIRMED
    assert confirmed.published is False


def test_cancel_sets_cancelled(tmp_path):
    svc, review, _, _ = _setup(tmp_path)
    _approved_item(review)
    slot = svc.propose_schedule()[0]
    cancelled = svc.cancel(slot.id, reason="changed plan")
    assert cancelled.status == SLOT_CANCELLED


def test_scheduler_never_publishes(tmp_path):
    svc, review, store, _ = _setup(tmp_path)
    _approved_item(review)
    slot = svc.propose_schedule()[0]
    svc.confirm(slot.id)
    # No slot is ever published, and there is no publish API.
    assert all(not s.published for s in store.list())
    assert not hasattr(ScheduledSlot, "publish")
    assert not hasattr(SchedulerService, "publish")
    assert not hasattr(SchedulerService, "post")


def test_actions_are_audited(tmp_path):
    svc, review, _, memory = _setup(tmp_path)
    _approved_item(review)
    slot = svc.propose_schedule()[0]
    svc.confirm(slot.id)
    audit = memory.read_audit()
    assert "schedule_proposed" in audit
    assert "schedule_confirmed" in audit


def test_confirm_missing_slot_raises(tmp_path):
    svc, _, _, _ = _setup(tmp_path)
    try:
        svc.confirm("sch-nope")
        assert False, "expected SchedulerError"
    except SchedulerError:
        pass
