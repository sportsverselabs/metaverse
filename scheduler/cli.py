"""Scheduler command-line interface. Proposes/confirms times. NEVER posts.

Usage (run from the project root):

    python -m scheduler propose            # create proposed times for approved items
    python -m scheduler list               # show slots (default: all)
    python -m scheduler list --status proposed
    python -m scheduler confirm <slot_id>  # owner confirms a time (still NOT published)
    python -m scheduler cancel <slot_id> --reason "..."

A "confirmed" slot only records WHEN an approved item should go out, for a future
publisher module. Nothing is posted by this tool.
"""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from scheduler.service import SchedulerError, SchedulerService


def _build_service() -> SchedulerService:
    from main import build_system  # local import avoids cycles at module import time

    _hermes, services = build_system()
    return SchedulerService(services["scheduler_store"], services["review_store"], memory=services["memory"])


def cmd_propose(service: SchedulerService, args) -> int:
    slots = service.propose_schedule()
    if not slots:
        print("No new approved items to schedule. (Approve items for scheduling via: python -m review schedule <id>)")
        return 0
    print(f"Proposed {len(slots)} slot(s):")
    for s in slots:
        print(f"  {s.id}  review={s.review_id}  skill={s.skill}  at={s.scheduled_for}  status={s.status}")
    print("\nNothing is published. Confirm a time with: python -m scheduler confirm <slot_id>")
    return 0


def cmd_list(service: SchedulerService, args) -> int:
    slots = service.list(status=args.status)
    label = args.status or "all"
    print(f"\nScheduler - slots ({label}): {len(slots)}\n")
    if not slots:
        print("  (none)")
    for s in slots:
        print(f"  {s.id}  [{s.status}]  at={s.scheduled_for}  review={s.review_id}  skill={s.skill}  published={s.published}")
    print()
    return 0


def cmd_confirm(service: SchedulerService, args) -> int:
    s = service.confirm(args.id)
    print(f"Confirmed {s.id} for {s.scheduled_for} (status={s.status}, published={s.published}). Nothing posted.")
    return 0


def cmd_cancel(service: SchedulerService, args) -> int:
    s = service.cancel(args.id, reason=args.reason or "")
    print(f"Cancelled {s.id} (status={s.status}).")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="scheduler", description="Sportsverse OS scheduler (proposes times; never posts).")
    sub = parser.add_subparsers(dest="command", required=True)

    p_prop = sub.add_parser("propose", help="propose times for approved items")
    p_prop.set_defaults(func=cmd_propose)

    p_list = sub.add_parser("list", help="list slots")
    p_list.add_argument("--status", default=None, help="filter: proposed | confirmed | cancelled")
    p_list.set_defaults(func=cmd_list)

    p_conf = sub.add_parser("confirm", help="confirm a proposed time (does NOT publish)")
    p_conf.add_argument("id")
    p_conf.set_defaults(func=cmd_confirm)

    p_canc = sub.add_parser("cancel", help="cancel a slot")
    p_canc.add_argument("id")
    p_canc.add_argument("--reason", default="", help="why it was cancelled")
    p_canc.set_defaults(func=cmd_cancel)

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    from core.console import enable_utf8_console
    enable_utf8_console()
    parser = build_parser()
    args = parser.parse_args(argv)
    service = _build_service()
    try:
        return args.func(service, args)
    except SchedulerError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
