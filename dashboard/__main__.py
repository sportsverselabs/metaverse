"""Run the owner dashboard:  python -m dashboard [--host H] [--port P]"""

from __future__ import annotations

import argparse

from core.console import enable_utf8_console
from dashboard.server import run_server


def main() -> int:
    enable_utf8_console()
    ap = argparse.ArgumentParser(prog="dashboard", description="SportVerse Labs owner dashboard (read-only).")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8787)
    args = ap.parse_args()
    run_server(args.host, args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
