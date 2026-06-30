"""Dashboard HTTP server (stdlib): login + Telegram 2FA + session-gated 14-section app.

Routes:
  GET  /dashboard            -> shell if session valid, else login page
  POST /dashboard/login      -> verify password, send 2FA code via Telegram, show verify page
  POST /dashboard/verify     -> verify code, issue session cookie
  GET  /dashboard/logout     -> clear session
  GET  /dashboard/api?section=NAME -> session-gated HTML fragment
  POST /dashboard/ask        -> session-gated; runs a command through Hermes (DeepSeek)
  POST /dashboard/action     -> session-gated; approve/reject/edit/schedule/publish a review item
  GET  /health               -> ok

Secrets, passwords, 2FA codes, and tokens are never logged.
"""

from __future__ import annotations

import json
import urllib.parse
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from core.config import load_config
from core.logging_setup import get_logger

_log = get_logger("dashboard")
_SESSION_COOKIE = "sv_session"
_PENDING_COOKIE = "sv_pending"

_auth = None  # shared AuthService (keeps 2FA + sessions across requests)


def _build_auth():
    from auth.service import AuthService
    config = load_config()

    def send_code(code, user):
        from integrations.telegram_bot import JarvisTelegramBot
        bot = JarvisTelegramBot(config=config)
        bot.send(f"Sportsverse dashboard sign-in code: {code}\nValid 5 minutes. "
                 f"If this wasn't you, ignore this message.")
    return AuthService(config=config, send_code=send_code)


def _handler_class():
    from dashboard import app as ui
    from dashboard.data import DashboardData

    class Handler(BaseHTTPRequestHandler):
        # -- helpers --
        def _cookies(self):
            c = SimpleCookie()
            if "Cookie" in self.headers:
                c.load(self.headers["Cookie"])
            return c

        def _session_user(self):
            c = self._cookies()
            tok = c[_SESSION_COOKIE].value if _SESSION_COOKIE in c else None
            return _auth.validate_session(tok)

        def _send(self, code, ctype, body, cookies=None):
            if isinstance(body, str):
                body = body.encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("X-Content-Type-Options", "nosniff")
            for ck in (cookies or []):
                self.send_header("Set-Cookie", ck)
            self.end_headers()
            self.wfile.write(body)

        def _redirect(self, location, cookies=None):
            self.send_response(303)
            self.send_header("Location", location)
            for ck in (cookies or []):
                self.send_header("Set-Cookie", ck)
            self.end_headers()

        def _body_json(self):
            n = int(self.headers.get("Content-Length", 0) or 0)
            raw = self.rfile.read(n) if n else b""
            try:
                return json.loads(raw or b"{}")
            except json.JSONDecodeError:
                return {}

        def _body_form(self):
            n = int(self.headers.get("Content-Length", 0) or 0)
            raw = self.rfile.read(n) if n else b""
            return {k: v[0] for k, v in urllib.parse.parse_qs(raw.decode("utf-8")).items()}

        def log_message(self, *a):
            return  # silence; never log request details (may contain codes)

        # -- GET --
        def do_GET(self):  # noqa: N802
            path = urllib.parse.urlparse(self.path).path
            qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if path in ("/health", "/healthz"):
                return self._send(200, "text/plain", b"ok")
            if path == "/dashboard/logout":
                return self._redirect("/dashboard", [f"{_SESSION_COOKIE}=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax"])
            if path == "/dashboard/api":
                if not self._session_user():
                    return self._send(401, "text/html", "<div class=note>Session expired. Reload.</div>")
                section = (qs.get("section", ["home"])[0])
                try:
                    return self._send(200, "text/html; charset=utf-8", ui.render_section(section, DashboardData()))
                except Exception as exc:
                    _log.error("section render failed: %s", section)
                    return self._send(200, "text/html", f"<div class=note>Could not load '{section}': {exc}</div>")
            if path == "/dashboard/studio":
                if not self._session_user():
                    return self._send(401, "text/html", "<div class=note>Session expired. Reload.</div>")
                from dashboard import studio
                pid = qs.get("project", [""])[0]
                return self._send(200, "text/html; charset=utf-8", studio.editor_html(pid))
            if path == "/dashboard/studio/media":
                if not self._session_user():
                    return self._send(401, "text/plain", b"unauthorized")
                from dashboard import studio
                resolved = studio.media_path(qs.get("project", [""])[0], qs.get("file", [""])[0])
                if not resolved:
                    return self._send(404, "text/plain", b"not found")
                target, ctype = resolved
                return self._send(200, ctype, target.read_bytes())
            # main entry (/, /dashboard, /dashboard/)
            if self._session_user():
                return self._send(200, "text/html; charset=utf-8", ui.shell_page(self._session_user()))
            if not _auth.configured:
                return self._send(200, "text/html; charset=utf-8",
                                  ui.login_page("Dashboard not configured yet (DASH_PASSWORD_HASH unset)."))
            return self._send(200, "text/html; charset=utf-8", ui.login_page())

        # -- POST --
        def do_POST(self):  # noqa: N802
            path = urllib.parse.urlparse(self.path).path
            if path == "/dashboard/login":
                f = self._body_form()
                pending = _auth.start_login(f.get("user", ""), f.get("password", ""))
                if not pending:
                    return self._send(200, "text/html; charset=utf-8", ui.login_page("Invalid credentials."))
                ck = f"{_PENDING_COOKIE}={pending}; Path=/dashboard; Max-Age=360; HttpOnly; SameSite=Lax"
                return self._send(200, "text/html; charset=utf-8", ui.verify_page(), [ck])
            if path == "/dashboard/verify":
                f = self._body_form()
                c = self._cookies()
                pending = c[_PENDING_COOKIE].value if _PENDING_COOKIE in c else ""
                token = _auth.verify_code(pending, f.get("code", ""))
                if not token:
                    return self._send(200, "text/html; charset=utf-8", ui.verify_page("Invalid or expired code."))
                cookies = [f"{_SESSION_COOKIE}={token}; Path=/; Max-Age=28800; HttpOnly; SameSite=Lax",
                           f"{_PENDING_COOKIE}=; Path=/dashboard; Max-Age=0; HttpOnly; SameSite=Lax"]
                return self._redirect("/dashboard", cookies)
            # gated endpoints
            if not self._session_user():
                return self._send(401, "application/json", json.dumps({"error": "unauthorized"}))
            if path == "/dashboard/ask":
                cmd = (self._body_json().get("command") or "").strip()
                if not cmd:
                    return self._send(200, "application/json", json.dumps({"error": "empty command"}))
                try:
                    from orchestration.langgraph_app import run_task
                    state = run_task(cmd, source="dashboard")
                    return self._send(200, "application/json", json.dumps({"report": state.report}))
                except Exception as exc:
                    _log.error("ask failed: %s", exc)
                    return self._send(200, "application/json", json.dumps({"error": f"Hermes error: {exc}"}))
            if path == "/dashboard/action":
                return self._do_action(self._body_json())
            if path == "/dashboard/studio/action":
                from dashboard import studio
                try:
                    result = studio.studio_action(self._body_json(), actor=self._session_user())
                except Exception as exc:
                    _log.error("studio action failed: %s", type(exc).__name__)
                    result = {"error": f"studio error: {type(exc).__name__}"}
                return self._send(200, "application/json", json.dumps(result))
            return self._send(404, "application/json", json.dumps({"error": "not found"}))

        def _do_action(self, body):
            from memory.manager import MemoryManager
            from review.service import ReviewError, ReviewService
            from review.store import ReviewStore
            store = ReviewStore()
            memory = MemoryManager()
            svc = ReviewService(store, memory=memory)
            iid = (body.get("id") or "").strip()
            action = (body.get("action") or "").strip()
            try:
                if action == "approve":
                    svc.approve(iid); msg = "Draft approved (not published)."
                elif action == "reject":
                    svc.reject(iid, body.get("reason") or "rejected via dashboard"); msg = "Rejected and archived."
                elif action == "edit":
                    svc.request_edit(iid, body.get("notes") or "please revise"); msg = "Revision requested."
                elif action == "schedule":
                    svc.approve_for_scheduled_publish(iid); msg = "Approved for scheduling (NOT published)."
                elif action == "publish":
                    platform = (body.get("platform") or "").strip().lower()
                    visibility = (body.get("visibility") or "private").strip().lower()
                    from publishing.service import PublishingService
                    result = PublishingService(config=load_config(), review_store=store,
                                               memory=memory).publish_review_item(
                                                   iid, platform=platform, visibility=visibility)
                    if not result.ok:
                        return self._send(200, "application/json", json.dumps({"error": result.reason}))
                    target = result.url or result.post_id or platform
                    msg = f"Published to {platform}: {target}"
                else:
                    return self._send(200, "application/json", json.dumps({"error": "unknown action"}))
                return self._send(200, "application/json", json.dumps({"message": msg}))
            except (ReviewError, ValueError) as exc:
                return self._send(200, "application/json", json.dumps({"error": str(exc)}))

    return Handler


def run_server(host: str = "127.0.0.1", port: int = 8787) -> None:
    global _auth
    _auth = _build_auth()
    httpd = ThreadingHTTPServer((host, port), _handler_class())
    status = "configured" if _auth.configured else "NOT configured (set DASH_PASSWORD_HASH)"
    print(f"Sportsverse dashboard on http://{host}:{port}  (auth: {status})  — Ctrl-C to stop")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nDashboard stopped.")
        httpd.server_close()
