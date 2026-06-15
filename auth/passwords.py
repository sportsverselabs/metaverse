"""Password hashing (PBKDF2-HMAC-SHA256, stdlib only).

Stored format: ``pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>``.
Never log or print passwords. The dashboard reads the HASH from `.env` (DASH_PASSWORD_HASH);
the plaintext password is never stored anywhere.
"""

from __future__ import annotations

import hashlib
import hmac
import os

_ITERATIONS = 240_000


def hash_password(password: str, *, iterations: int = _ITERATIONS) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2_sha256${iterations}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, iters, salt_hex, hash_hex = stored.split("$")
        if algo != "pbkdf2_sha256":
            return False
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iters))
        return hmac.compare_digest(dk.hex(), hash_hex)
    except (ValueError, AttributeError):
        return False
