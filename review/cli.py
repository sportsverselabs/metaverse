"""Owner-review command-line interface.

A simple, safe surface for the owner to review drafts. No publishing — ever.

Usage (run from the project root):

    python -m review list                        # pending drafts awaiting review
    python -m review list --status owner_approved
    python -m review show <id>                    # full draft + compliance + gates + history
    python -m review approve <id>                 # approve the DRAFT only -> owner_approved
    python -m review revise <id> --notes "..."    # request a revision (creates a Hermes task)
    python -m review reject <id> --reason "..."   # archive with reason -> owner_rejected
    python -m review schedule <id>                # approve for scheduled publish (6 gates) -> NOT published

The four owner choices map to:
    1. Approve draft only            -> approve
    2. Request revision              -> revise
    3. Reject                        -> reject
    4. Approve for scheduled publish -> schedule  (only if all 6 gates pass; still NOT published)
"""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from review.models import STATUS_READY
from review.service import ReviewError, ReviewService


def _build_service() -> ReviewService:
    """Assemble the system and a review service over the real store."""
    from main import build_system  # local import to avoid cycles at module import time

    hermes, services = build_system()
    return ReviewService(services["review_store"], memory=services["memory"], reviser=hermes)


def _print_row(item) -> None:
    snippet = " ".join((item.content or "").split())[:70]
    print(f"  {item.id}  [{item.status}]  skill={item.skill}  risk={item.risk_score}/100")
    print(f"      created={item.created}  preview: {snippet}")


def cmd_list(service: ReviewService, args) -> int:
    status = args.status or STATUS_READY
    items = service.list(status=status, include_archived=args.all)
    title = "ALL items" if args.all else f"items with status '{status}'"
    print(f"\nOwner review - {title} ({len(items)}):\n")
    if not items:
        print("  (none)")
    for item in items:
        _print_row(item)
    print("\nReminder: nothing is ever published here. 'schedule' only clears items for a")
    print("future scheduler/publisher module that requires its own separate approval.\n")
    return 0


def cmd_show(service: ReviewService, args) -> int:
    item = service.get(args.id)
    print(f"\n=== Review item {item.id} ===")
    print(f"status     : {item.status}")
    print(f"skill      : {item.skill}")
    print(f"risk score : {item.risk_score}/100  (compliance passed gate: {item.compliance.get('passed')})")
    print(f"published  : {item.published}  (always False in this phase)")
    print(f"compliance : {item.compliance}")
    print("\ngates:")
    for name, passed in (item.gates or {}).items():
        print(f"  [{'x' if passed else ' '}] {name}")
    print("\n--- draft content ---")
    print(item.content)
    print("--- end draft ---")
    print("\nhistory:")
    for h in item.history:
        print(f"  {h['ts']}  {h['action']:<28} by={h['by']}  {h.get('notes','')}")
    print()
    return 0


def cmd_approve(service: ReviewService, args) -> int:
    item = service.approve(args.id)
    print(f"Approved DRAFT {item.id} -> {item.status} (NOT scheduled, NOT published). published={item.published}")
    return 0


def cmd_reject(service: ReviewService, args) -> int:
    item = service.reject(args.id, args.reason)
    print(f"Rejected and archived {item.id} -> {item.status}. Reason: {args.reason}")
    return 0


def cmd_revise(service: ReviewService, args) -> int:
    out = service.request_revision(args.id, args.notes)
    item = out["item"]
    result = out["result"]
    print(f"Revision requested for {item.id} -> {item.status}.")
    if result is not None:
        print(f"  New revised draft produced: status={result.status} "
              f"review_id={result.data.get('review_id')}")
    else:
        print("  Revision task created (not auto-run).")
    return 0


def cmd_schedule(service: ReviewService, args) -> int:
    item = service.approve_for_scheduled_publish(args.id)
    print(f"{item.id} -> {item.status}")
    print(f"  Cleared for a FUTURE scheduler ONLY. published={item.published} (still not published).")
    return 0


def cmd_reconcile(service: ReviewService, args) -> int:
    """Detect (and with --apply, safely reject) orphaned gated actions with no backing draft."""
    from review.reconcile import reconcile
    result = reconcile(apply=args.apply)
    orphans = result["orphaned"]
    if not orphans:
        print("No orphaned gated actions. Approvals is consistent.")
        return 0
    print(f"Found {len(orphans)} orphaned gated action(s):")
    for o in orphans:
        print(f"  {o['id']}  {o['action']}  (task {o['task_id'] or '—'}) — {o['reason']}")
    if args.apply:
        print(f"Rejected {len(result['rejected'])} orphaned action(s) (reversible; records retained).")
    else:
        print("Dry run. Re-run with --apply to reject these orphaned actions. Nothing publishes.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="review", description="Sportsverse OS owner-review surface (no publishing).")
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="list review items (default: pending)")
    p_list.add_argument("--status", default=None, help="filter by status")
    p_list.add_argument("--all", action="store_true", help="include archived (rejected) items")
    p_list.set_defaults(func=cmd_list)

    p_show = sub.add_parser("show", help="show one item in full (incl. gates)")
    p_show.add_argument("id")
    p_show.set_defaults(func=cmd_show)

    p_approve = sub.add_parser("approve", help="approve the DRAFT only (-> owner_approved)")
    p_approve.add_argument("id")
    p_approve.set_defaults(func=cmd_approve)

    p_revise = sub.add_parser("revise", help="request a revision (creates a Hermes task)")
    p_revise.add_argument("id")
    p_revise.add_argument("--notes", required=True, help="what to change")
    p_revise.set_defaults(func=cmd_revise)

    p_reject = sub.add_parser("reject", help="reject and archive with a reason")
    p_reject.add_argument("id")
    p_reject.add_argument("--reason", required=True, help="why it was rejected")
    p_reject.set_defaults(func=cmd_reject)

    p_sched = sub.add_parser("schedule", help="approve for scheduled publish (6 gates; NOT published)")
    p_sched.add_argument("id")
    p_sched.set_defaults(func=cmd_schedule)

    p_rec = sub.add_parser("reconcile", help="find/clear orphaned gated actions (no backing draft)")
    p_rec.add_argument("--apply", action="store_true", help="reject the orphaned actions (reversible)")
    p_rec.set_defaults(func=cmd_reconcile)

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    from core.console import enable_utf8_console
    enable_utf8_console()
    parser = build_parser()
    args = parser.parse_args(argv)
    service = _build_service()
    try:
        return args.func(service, args)
    except ReviewError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
