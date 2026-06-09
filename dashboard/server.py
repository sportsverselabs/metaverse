"""Read-only dashboard HTTP server (Python stdlib only)."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer

from core.logging_setup import get_logger

_log = get_logger("dashboard")


def _build_handler():
    from agents.dashboard_agent import DashboardAgent
    from dashboard.render import render_html

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            try:
                data = DashboardAgent().assemble_data()
            except Exception as exc:  # never crash the server
                self._send(500, "text/plain", f"dashboard error: {exc}".encode())
                return
            if self.path.startswith("/data"):
                self._send(200, "application/json", json.dumps(data, default=str).encode())
            elif self.path in ("/health", "/healthz"):
                self._send(200, "text/plain", b"ok")
            else:
                self._send(200, "text/html; charset=utf-8", render_html(data).encode("utf-8"))

        def _send(self, code, ctype, body):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):  # silence default request logging
            return

    return Handler


def run_server(host: str = "127.0.0.1", port: int = 8787) -> None:
    handler = _build_handler()
    httpd = HTTPServer((host, port), handler)
    print(f"Dashboard (read-only) at http://{host}:{port}  — Ctrl-C to stop")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nDashboard stopped.")
        httpd.server_close()
