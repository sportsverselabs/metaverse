"""Phase 2C smoke test (mock mode, isolated temp dirs, no publishing).

Demonstrates the full gated owner-review flow end to end:
  1. drafts created via Hermes pipeline (mock LLM)
  2. compliance reviewed (risk score + pass/fail)
  3. drafts appear in the owner-review surface
  4. owner: approve draft only / reject / request revision / approve-for-scheduled-publish
  5. the 6 gates are enforced; compliance failure blocks scheduling
  6. NOTHING publishes (published stays False; scheduled status only clears for a FUTURE scheduler)

Run from the project root:  python scripts/smoke_review.py
"""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

# Make the project root importable when run as `python scripts/smoke_review.py`.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agents.base import Task
from agents.compliance import Compliance
from agents.hermes import Hermes
from agents.openclaw import OpenClaw
from agents.sentinel import Sentinel
from core.llm_router import LLMRouter
from core.logging_setup import setup_logging
from memory.manager import MemoryManager
from review.models import STATUS_SCHEDULED, make_review_item
from review.service import ReviewError, ReviewService
from review.store import ReviewStore
from skills.registry import default_registry


def banner(text: str) -> None:
    print("\n" + "=" * 66)
    print(text)
    print("=" * 66)


def main() -> None:
    setup_logging("warning")  # quiet logs so the demo output is readable
    tmp = Path(tempfile.mkdtemp(prefix="sv_smoke_"))
    try:
        memory = MemoryManager(store_dir=tmp / "mem")
        store = ReviewStore(base_dir=tmp / "review")
        shared = {"config": None, "memory": memory, "llm": LLMRouter()}  # mock mode
        hermes = Hermes(review_store=store, **shared)
        hermes.register(OpenClaw(registry=default_registry(), **shared))
        hermes.register(Sentinel(**shared))
        hermes.register(Compliance(**shared))
        service = ReviewService(store, memory=memory, reviser=hermes)

        banner("STEP 1-3: create drafts (mock) -> compliance review -> owner-review queue")
        d1 = hermes.handle(Task(name="request", payload={"text": "draft a daily report"}))
        d2 = hermes.handle(Task(name="request", payload={"text": "draft some video ideas about the finals"}))
        d3 = hermes.handle(Task(name="request", payload={"text": "draft a script outline for a highlight"}))
        d4 = hermes.handle(Task(name="request", payload={"text": "research trending sports topics"}))
        for d in (d1, d2, d3, d4):
            print(f"  {d.data['review_id']}  status={d.status}  skill={d.data['skill']}  "
                  f"risk={d.data['risk_score']}  published={d.data['published']}")

        banner("STEP 4: the four owner choices")
        a = service.approve(d1.data["review_id"])
        print(f"  1) APPROVE DRAFT ONLY   {a.id} -> {a.status}  published={a.published}")
        r = service.reject(d2.data["review_id"], reason="off-brand for Platinum Clips")
        print(f"  3) REJECT               {r.id} -> {r.status}  (archived with reason)")
        out = service.request_revision(d3.data["review_id"], notes="tighten the hook, add a CTA")
        print(f"  2) REQUEST REVISION     {out['item'].id} -> {out['item'].status}")
        print(f"                          new revised draft: {out['result'].data['review_id']}")
        s = service.approve_for_scheduled_publish(d4.data["review_id"])
        print(f"  4) APPROVE-FOR-SCHEDULE {s.id} -> {s.status}  published={s.published}")
        print(f"                          gates: {s.gates}")

        banner("STEP 5: the 6 gates block scheduling when compliance fails")
        bad = make_review_item("affiliate_product_research_draft", "buy now, guaranteed results!", 80,
                               {"verdict": "needs_human_review", "risk_score": 80, "passed": False},
                               compliance_passed=False)
        store.add(bad)
        try:
            service.approve_for_scheduled_publish(bad.id)
            print("  ERROR: high-risk item was scheduled (should not happen!)")
        except ReviewError as exc:
            print(f"  BLOCKED as expected: {exc}")

        banner("STEP 6: verify NO publishing occurred")
        all_items = store.list(include_archived=True)
        any_published = any(i.published for i in all_items)
        print(f"  total items: {len(all_items)}  | any published? {any_published}")
        print(f"  scheduled item status == '{STATUS_SCHEDULED}': {s.status == STATUS_SCHEDULED}")
        print(f"  scheduled item published flag: {s.published}")

        print("\n  Structured audit log (one JSON record per action):")
        for line in memory.read_audit().splitlines():
            print("    " + line.strip())

        banner("RESULT")
        assert not any_published, "INVARIANT VIOLATED: something was published!"
        print("  OK: drafts created, compliance-reviewed, queued; all four owner actions worked.")
        print("  OK: 6-gate scheduling enforced; compliance failure blocked scheduling.")
        print("  OK: nothing published. 'approved_for_scheduled_publish' only clears for a future scheduler.")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
