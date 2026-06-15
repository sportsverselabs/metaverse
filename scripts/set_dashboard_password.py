"""Generate dashboard credentials for .env.

    python scripts/set_dashboard_password.py [password]

Prints the lines to put in .env (DASH_USER / DASH_PASSWORD_HASH / SESSION_SECRET).
If no password is given, a strong one is generated and shown ONCE. The plaintext password
is never stored — only its hash goes in .env.
"""

from __future__ import annotations

import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from auth.passwords import hash_password


def main() -> int:
    pw = sys.argv[1] if len(sys.argv) > 1 else secrets.token_urlsafe(12)
    print("# --- Add these to .env (dashboard login) ---")
    print("DASH_USER=owner")
    print("DASH_PASSWORD_HASH=" + hash_password(pw))
    print("SESSION_SECRET=" + secrets.token_hex(32))
    print()
    print(f"# Dashboard login password (save it now; not stored anywhere): {pw}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
