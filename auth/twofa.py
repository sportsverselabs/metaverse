"""Telegram 2FA challenge store (stdlib only).

After a correct password, a 6-digit code is generated and sent to the owner's Telegram. The
code is held (hashed) in memory with an expiry and a max-attempts limit, then verified. The
code is NEVER logged. Single-process in-memory store (fine for the systemd dashboard service);
if the server restarts mid-login, the owner simply logs in again.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import time
import uuid

_TTL = 300          # code valid 5 minutes
_MAX_ATTEMPTS = 5


def _hash(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


class TwoFactorStore:
    def __init__(self) -> None:
        self._pending: dict[str, dict] = {}

    def new_challenge(self, user: str) -> tuple[str, str]:
        """Create a challenge. Returns (pending_id, code). Caller sends the code via Telegram."""
        self._gc()
        code = f"{secrets.randbelow(1_000_000):06d}"
        pending_id = uuid.uuid4().hex
        self._pending[pending_id] = {
            "user": user, "code_hash": _hash(code),
            "exp": time.time() + _TTL, "attempts": 0,
        }
        return pending_id, code

    def verify(self, pending_id: str, code: str) -> str | None:
        """Return the username on success, else None. Consumes the challenge on success."""
        ch = self._pending.get(pending_id)
        if not ch:
            return None
        if time.time() > ch["exp"] or ch["attempts"] >= _MAX_ATTEMPTS:
            self._pending.pop(pending_id, None)
            return None
        ch["attempts"] += 1
        if hmac.compare_digest(ch["code_hash"], _hash(code or "")):
            self._pending.pop(pending_id, None)
            return ch["user"]
        return None

    def _gc(self) -> None:
        now = time.time()
        for pid in [p for p, c in self._pending.items() if c["exp"] < now]:
            self._pending.pop(pid, None)
