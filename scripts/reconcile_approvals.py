"""Repair script: reconcile orphaned gated actions against draft/review records.

An orphaned gated action is a pending approval (e.g. `publish_content`) with no backing draft in the
review store — it clutters Approvals with nothing to act on. This safely rejects them (reversible;
the record files are retained). Nothing publishes.

    python scripts/reconcile_approvals.py            # dry run (report only)
    python scripts/reconcile_approvals.py --apply     # reject orphaned actions

Equivalent to: python -m review reconcile [--apply]
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.console import enable_utf8_console
from review.reconcile import reconcile


def main() -> int:
    enable_utf8_console()
    apply = "--apply" in sys.argv
    result = reconcile(apply=apply)
    orphans = result["orphaned"]
    if not orphans:
        print("No orphaned gated actions. Approvals is consistent.")
        return 0
    print(f"Found {len(orphans)} orphaned gated action(s):")
    for o in orphans:
        print(f"  {o['id']}  {o['action']}  (task {o['task_id'] or '—'}) — {o['reason']}")
    if apply:
        print(f"Rejected {len(result['rejected'])} orphaned action(s) (reversible; records retained).")
    else:
        print("Dry run — re-run with --apply to clear these. Nothing publishes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
