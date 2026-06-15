"""Stateless signed session tokens (HMAC-SHA256, stdlib only).

Token = base64url(payload_json) + "." + base64url(hmac(secret, payload)). Survives restarts,
needs no server store, and carries an expiry. The signing secret comes from SESSION_SECRET
(`.env`); if absent, a random per-process secret is generated (sessions then reset on restart).
Never log the secret or tokens.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time


def _b64e(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode("ascii").rstrip("=")


def _b64d(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


class SessionManager:
    def __init__(self, secret: str | None = None) -> None:
        if not secret:
            secret = os.urandom(32).hex()  # ephemeral; set SESSION_SECRET in .env for persistence
        self._secret = secret.encode("utf-8")

    def _sign(self, payload_b64: str) -> str:
        return _b64e(hmac.new(self._secret, payload_b64.encode("ascii"), hashlib.sha256).digest())

    def issue(self, user: str, ttl_seconds: int = 8 * 3600) -> str:
        payload = {"u": user, "exp": int(time.time()) + ttl_seconds}
        payload_b64 = _b64e(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
        return f"{payload_b64}.{self._sign(payload_b64)}"

    def validate(self, token: str | None) -> str | None:
        if not token or "." not in token:
            return None
        payload_b64, sig = token.split(".", 1)
        if not hmac.compare_digest(sig, self._sign(payload_b64)):
            return None
        try:
            data = json.loads(_b64d(payload_b64))
        except (ValueError, json.JSONDecodeError):
            return None
        if int(data.get("exp", 0)) < int(time.time()):
            return None
        return data.get("u")
