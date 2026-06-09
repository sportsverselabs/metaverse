"""Jarvis CLI entry point: route a natural-language command through the Hermes core.

    python -m orchestration "research trending NBA storylines for short-form video"

Nothing is published, sent, or spent. Gated actions become pending approvals.
"""

from __future__ import annotations

import sys

from orchestration.langgraph_app import engine_name, run_task


def main(argv=None) -> int:
    # Make console output robust to non-ASCII model text on any platform (e.g. Windows cp1252).
    from core.console import enable_utf8_console
    enable_utf8_console()

    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        print('Usage: python -m orchestration "<your request>"')
        return 2
    request = " ".join(argv)
    print(f"[Jarvis] engine={engine_name()}  request={request!r}\n")
    state = run_task(request, source="cli")
    print(state.report)
    print(f"\n(task_id={state.task_id}, path={' -> '.join(state.path)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
