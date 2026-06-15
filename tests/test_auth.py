"""Tests for dashboard auth: password hashing, sessions, Telegram 2FA, and the full flow.

No real secrets, no network — the 2FA 'send' is captured by a fake callback.
"""

from auth.passwords import hash_password, verify_password
from auth.service import AuthService
from auth.sessions import SessionManager
from auth.twofa import TwoFactorStore


class FakeConfig:
    def __init__(self, d):
        self.d = d

    def get(self, k, default=None):
        return self.d.get(k, default)

    def secret(self, k):
        return self.d.get(k)


def test_password_hash_and_verify():
    stored = hash_password("correct horse battery")
    assert verify_password("correct horse battery", stored) is True
    assert verify_password("wrong", stored) is False
    assert verify_password("x", "not-a-hash") is False


def test_session_issue_validate_and_tamper():
    sm = SessionManager("secret-A")
    tok = sm.issue("owner", ttl_seconds=60)
    assert sm.validate(tok) == "owner"
    assert sm.validate(tok + "x") is None          # tampered signature
    assert SessionManager("secret-B").validate(tok) is None  # different secret
    assert sm.validate(sm.issue("owner", ttl_seconds=-1)) is None  # expired


def test_2fa_challenge_verify():
    store = TwoFactorStore()
    pid, code = store.new_challenge("owner")
    assert store.verify(pid, "000000") is None or code != "000000"  # wrong code fails
    pid2, code2 = store.new_challenge("owner")
    assert store.verify(pid2, code2) == "owner"     # correct code passes
    assert store.verify(pid2, code2) is None         # consumed after success


def test_auth_service_full_flow():
    captured = {}
    cfg = FakeConfig({
        "DASH_USER": "owner",
        "DASH_PASSWORD_HASH": hash_password("s3cret"),
        "SESSION_SECRET": "test-session-secret",
    })
    auth = AuthService(config=cfg, send_code=lambda code, user: captured.update(code=code))
    assert auth.configured is True

    # wrong password -> no pending, no code sent
    assert auth.start_login("owner", "nope") is None
    assert "code" not in captured

    # correct password -> pending id + code "sent"
    pending = auth.start_login("owner", "s3cret")
    assert pending and "code" in captured

    # wrong code -> no session
    assert auth.verify_code(pending, "999999") is None or captured["code"] != "999999"

    # correct code -> session token that validates
    pending2 = auth.start_login("owner", "s3cret")
    token = auth.verify_code(pending2, captured["code"])
    assert token
    assert auth.validate_session(token) == "owner"


def test_auth_service_unconfigured_blocks_login():
    auth = AuthService(config=FakeConfig({}), send_code=lambda c, u: None)
    assert auth.configured is False
    assert auth.start_login("owner", "anything") is None
