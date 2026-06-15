"""AuthService — login (password) + Telegram 2FA + session issuance.

Flow:
  1. start_login(user, password) -> verify password -> generate code -> send via Telegram -> return pending_id
  2. verify_code(pending_id, code) -> issue signed session token
  3. validate_session(token) -> user | None

Reads DASH_USER (default 'owner'), DASH_PASSWORD_HASH, SESSION_SECRET from config/.env.
Never logs passwords, codes, secrets, or tokens.
"""

from __future__ import annotations

from typing import Callable, Optional

from auth.passwords import verify_password
from auth.sessions import SessionManager
from auth.twofa import TwoFactorStore
from core.logging_setup import get_logger


class AuthService:
    def __init__(self, config=None, send_code: Optional[Callable[[str, str], None]] = None, logger=None) -> None:
        self.config = config
        self.log = logger or get_logger("auth")
        self._user = (config.get("DASH_USER") if config else None) or "owner"
        self._pw_hash = (config.secret("DASH_PASSWORD_HASH") if config else None) or ""
        self._sessions = SessionManager(config.secret("SESSION_SECRET") if config else None)
        self._twofa = TwoFactorStore()
        # send_code(code, user) -> delivers the 6-digit code to the owner (e.g. via Telegram)
        self._send_code = send_code

    @property
    def configured(self) -> bool:
        return bool(self._pw_hash)

    def start_login(self, user: str, password: str) -> Optional[str]:
        """Verify credentials; if ok, send a 2FA code and return a pending id. Else None."""
        if not self.configured:
            self.log.warning("Dashboard login attempted but DASH_PASSWORD_HASH is not set.")
            return None
        ok_user = (user or "").strip() == self._user
        ok_pw = verify_password(password or "", self._pw_hash)
        if not (ok_user and ok_pw):
            self.log.info("Failed dashboard login (bad credentials).")  # no values logged
            return None
        pending_id, code = self._twofa.new_challenge(self._user)
        if self._send_code is not None:
            try:
                self._send_code(code, self._user)
            except Exception:
                self.log.error("Failed to send 2FA code via Telegram.")  # never log the code
                return None
        self.log.info("Dashboard password OK; 2FA code sent.")
        return pending_id

    def verify_code(self, pending_id: str, code: str) -> Optional[str]:
        """Verify the 2FA code; on success return a session token."""
        user = self._twofa.verify(pending_id, code)
        if not user:
            self.log.info("Failed 2FA verification.")
            return None
        self.log.info("Dashboard 2FA verified; session issued.")
        return self._sessions.issue(user)

    def validate_session(self, token: Optional[str]) -> Optional[str]:
        return self._sessions.validate(token)
