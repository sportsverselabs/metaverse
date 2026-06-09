"""Owner dashboard (read-only). Serves the system state over a stdlib HTTP server.

Read-only by design: approving/rejecting/publishing happens via Telegram or the CLIs so the
dashboard isn't an action surface that could publish. Run: ``python -m dashboard``.
"""

from dashboard.render import render_html  # noqa: F401
from dashboard.server import run_server  # noqa: F401

__all__ = ["render_html", "run_server"]
