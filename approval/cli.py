"""Approval queue CLI. Owner approves/rejects gated actions. Approval != execution.

    python -m approval list
    python -m approval list --status pending
    python -m approval approve <id>
    python -m approval reject <id> --reason "..."
"""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from approval.approval_queue import APPROVAL_PENDING, ApprovalQueue
from core.paths import APPROVALS_DIR


def _queue() -> ApprovalQueue:
    try:
        from memory.manager import MemoryManager
        return ApprovalQueue(base_dir=APPROVALS_DIR, memory=MemoryManager())
    except Exception:
        return ApprovalQueue(base_dir=APPROVALS_DIR)


def cmd_list(q: ApprovalQueue, args) -> int:
    items = q.list(status=args.status)
    label = args.status or "all"
    print(f"\nApproval queue ({label}): {len(items)}\n")
    if not items:
        print("  (none)")
    for r in items:
        print(f"  {r.id}  [{r.status}]  action={r.action}  task={r.task_id}")
        print(f"      reason: {r.reason}")
    print("\nApproving records intent only. No publishing/spending happens automatically.\n")
    return 0


def cmd_approve(q: ApprovalQueue, args) -> int:
    r = q.approve(args.id)
    print(f"Approved {r.id} ({r.action}). Status={r.status}. (Execution remains a separate, gated step.)")
    return 0


def cmd_reject(q: ApprovalQueue, args) -> int:
    r = q.reject(args.id, reason=args.reason or "")
    print(f"Rejected {r.id} ({r.action}). Status={r.status}.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="approval", description="Sportsverse OS approval queue (gated actions).")
    sub = p.add_subparsers(dest="command", required=True)
    pl = sub.add_parser("list", help="list approval requests")
    pl.add_argument("--status", default=None, help="pending | approved | rejected")
    pl.set_defaults(func=cmd_list)
    pa = sub.add_parser("approve", help="approve a request (records intent; does not execute)")
    pa.add_argument("id")
    pa.set_defaults(func=cmd_approve)
    pr = sub.add_parser("reject", help="reject a request")
    pr.add_argument("id")
    pr.add_argument("--reason", default="")
    pr.set_defaults(func=cmd_reject)
    return p


def main(argv: Optional[list[str]] = None) -> int:
    from core.console import enable_utf8_console
    enable_utf8_console()
    args = build_parser().parse_args(argv)
    q = _queue()
    try:
        return args.func(q, args)
    except KeyError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
