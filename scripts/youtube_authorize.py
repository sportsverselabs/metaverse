"""One-time YouTube OAuth authorizer — mints the refresh token the publisher needs.

Run this AFTER you've created an OAuth **Desktop app** client in Google Cloud Console (see
docs/YOUTUBE_SETUP_HANDOFF.md). It opens the Google consent screen in your browser, captures the
result on a local loopback port, exchanges it for a long-lived **refresh token**, and prints the three
lines to add to `.env`:

    YOUTUBE_CLIENT_ID=...
    YOUTUBE_CLIENT_SECRET=...
    YOUTUBE_REFRESH_TOKEN=...

Usage:
    python scripts/youtube_authorize.py --client-secrets /path/to/client_secret_xxx.json
    python scripts/youtube_authorize.py --client-id <id> --client-secret <secret>
    # add --write to append the three lines straight into ./.env (deduped)

Stdlib only. The client secret/refresh token are printed once for you to store; nothing is logged.
Scope requested: youtube.upload (least privilege needed to upload videos).
"""

from __future__ import annotations

import argparse
import http.server
import json
import socket
import sys
import threading
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
SCOPE = "https://www.googleapis.com/auth/youtube.upload"
_KEYS = ("YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET", "YOUTUBE_REFRESH_TOKEN")


def _load_client(args) -> tuple[str, str]:
    if args.client_secrets:
        data = json.loads(Path(args.client_secrets).read_text(encoding="utf-8"))
        node = data.get("installed") or data.get("web") or {}
        cid, csec = node.get("client_id"), node.get("client_secret")
        if not (cid and csec):
            sys.exit("client_secrets file has no client_id/client_secret (use a Desktop-app OAuth client).")
        return cid, csec
    if args.client_id and args.client_secret:
        return args.client_id, args.client_secret
    sys.exit("Provide --client-secrets <json> OR --client-id and --client-secret.")


def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class _Catcher(http.server.BaseHTTPRequestHandler):
    code = None
    error = None

    def do_GET(self):  # noqa: N802
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        _Catcher.code = (qs.get("code") or [None])[0]
        _Catcher.error = (qs.get("error") or [None])[0]
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        msg = "Authorization complete. You can close this tab and return to the terminal."
        if _Catcher.error:
            msg = f"Authorization failed: {_Catcher.error}. Close this tab and retry."
        self.wfile.write(f"<html><body style='font-family:sans-serif'><h3>Sportsverse</h3><p>{msg}</p></body></html>".encode())

    def log_message(self, *a):
        return  # never log (may contain the auth code)


def _exchange(client_id: str, client_secret: str, code: str, redirect_uri: str) -> dict:
    body = urllib.parse.urlencode({
        "code": code, "client_id": client_id, "client_secret": client_secret,
        "redirect_uri": redirect_uri, "grant_type": "authorization_code",
    }).encode()
    req = urllib.request.Request(TOKEN_URL, data=body,
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _write_env(lines: list[str]) -> None:
    env = Path(".env")
    existing = env.read_text(encoding="utf-8").splitlines() if env.exists() else []
    keep = [ln for ln in existing if ln.split("=", 1)[0].strip() not in _KEYS]
    env.write_text("\n".join(keep + lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Mint a YouTube refresh token (one-time).")
    ap.add_argument("--client-secrets", help="path to the downloaded client_secret_*.json")
    ap.add_argument("--client-id")
    ap.add_argument("--client-secret")
    ap.add_argument("--write", action="store_true", help="append the 3 lines into ./.env (deduped)")
    args = ap.parse_args()

    client_id, client_secret = _load_client(args)
    port = _free_port()
    redirect_uri = f"http://127.0.0.1:{port}/"
    auth_url = f"{AUTH_URL}?" + urllib.parse.urlencode({
        "client_id": client_id, "redirect_uri": redirect_uri, "response_type": "code",
        "scope": SCOPE, "access_type": "offline", "prompt": "consent",
    })

    server = http.server.HTTPServer(("127.0.0.1", port), _Catcher)
    threading.Thread(target=server.handle_request, daemon=True).start()

    print("\nOpening the Google consent screen in your browser...")
    print("Sign in as the channel owner (e.g. sportverselabs@gmail.com) and click Allow.")
    print(f"If it doesn't open, paste this URL into your browser:\n{auth_url}\n")
    try:
        webbrowser.open(auth_url)
    except Exception:
        pass

    # Wait for the loopback to capture the code.
    import time
    for _ in range(300):  # up to ~5 minutes
        if _Catcher.code or _Catcher.error:
            break
        time.sleep(1)
    server.server_close()

    if _Catcher.error or not _Catcher.code:
        print(f"Authorization did not complete ({_Catcher.error or 'no code received'}).")
        return 1

    tokens = _exchange(client_id, client_secret, _Catcher.code, redirect_uri)
    refresh = tokens.get("refresh_token")
    if not refresh:
        print("No refresh_token returned. Re-run (ensure prompt=consent / first-time grant).")
        print("Tip: revoke the app at https://myaccount.google.com/permissions then retry.")
        return 1

    lines = [f"YOUTUBE_CLIENT_ID={client_id}",
             f"YOUTUBE_CLIENT_SECRET={client_secret}",
             f"YOUTUBE_REFRESH_TOKEN={refresh}"]
    if args.write:
        _write_env(lines)
        print("\n✅ Wrote YOUTUBE_CLIENT_ID / YOUTUBE_CLIENT_SECRET / YOUTUBE_REFRESH_TOKEN to ./.env")
    else:
        print("\n✅ Success. Add these three lines to your .env (server-side only; never commit):\n")
        print("\n".join(lines))
    print("\nThen the dashboard Publishing page will show YouTube as connected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
