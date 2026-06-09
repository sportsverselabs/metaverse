"""Phase 3 scheduler smoke test (mock mode, isolated temp dirs, NO publishing).

Demonstrates: draft -> compliance -> owner approves for scheduled publish -> scheduler proposes
a time -> owner confirms the time -> NOTHING is published.

Run from the project root:  python scripts/smoke_scheduler.py
"""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agents.base import Task
from agents.compliance import Compliance
from agents.hermes import Hermes
from agents.openclaw import OpenClaw
from agents.sentinel import Sentinel
from core.llm_router import LLMRouter
from core.logging_setup import setup_logging
from memory.manager import MemoryManager
from review.service import ReviewService
from review.store import ReviewStore
from scheduler.service import SchedulerService
from scheduler.store import SchedulerStore
from skills.registry import default_registry


def banner(text: str) -> None:
    print("\n" + "=" * 66)
    print(text)
    print("=" * 66)


def main() -> None:
    setup_logging("warning")
    tmp = Path(tempfile.mkdtemp(prefix="sv_sched_"))
    try:
        memory = MemoryManager(store_dir=tmp / "mem")
        review_store = ReviewStore(base_dir=tmp / "review")
        sched_store = SchedulerStore(base_dir=tmp / "schedule")
        shared = {"config": None, "memory": memory, "llm": LLMRouter()}  # mock mode
        hermes = Hermes(review_store=review_store, **shared)
        hermes.register(OpenClaw(registry=default_registry(), **shared))
        hermes.register(Sentinel(**shared))
        hermes.register(Compliance(**shared))
        review = ReviewService(review_store, memory=memory, reviser=hermes)
        scheduler = SchedulerService(sched_store, review_store, memory=memory)

        banner("STEP 1: draft -> compliance -> owner approves FOR SCHEDULED PUBLISH")
        d = hermes.handle(Task(name="request", payload={"text": "draft a daily report"}))
        rid = d.data["review_id"]
        print(f"  draft {rid} status={d.status} risk={d.data['risk_score']} published={d.data['published']}")
        approved = review.approve_for_scheduled_publish(rid)
        print(f"  owner -> {approved.status}  published={approved.published} (6 gates passed)")

        banner("STEP 2: scheduler PROPOSES a time (does not post)")
        slots = scheduler.propose_schedule()
        slot = slots[0]
        print(f"  proposed {slot.id}  at={slot.scheduled_for}  status={slot.status}  published={slot.published}")

        banner("STEP 3: owner CONFIRMS the time (still does not post)")
        confirmed = scheduler.confirm(slot.id)
        print(f"  confirmed {confirmed.id}  status={confirmed.status}  published={confirmed.published}")

        banner("STEP 4: verify NOTHING published")
        all_slots = sched_store.list()
        any_pub = any(s.published for s in all_slots) or any(i.published for i in review_store.list(include_archived=True))
        print(f"  slots: {len(all_slots)}  | any published anywhere? {any_pub}")
        print("\n  Audit trail (schedule_* events):")
        for line in memory.read_audit().splitlines():
            if "schedule_" in line:
                print("    " + line.strip())

        banner("RESULT")
        assert not any_pub, "INVARIANT VIOLATED: something was published!"
        print("  OK: approved -> time proposed -> time confirmed. Nothing was posted.")
        print("  A confirmed slot is only a PLAN for a future, separately-approved publisher.")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
