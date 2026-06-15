"""Generate / set dashboard credentials.

    python scripts/set_dashboard_password.py            # print lines for .env (also shows password)
    python scripts/set_dashboard_password.py --write    # write them into ./.env (dedupes old ones)

Password source: $DASH_PW env var, else first arg, else a strong generated one (shown once).
DASH_PASSWORD_HASH and SESSION_SECRET are generated here; the plaintext password is never stored.
With --write, only non-secret confirmation is printed (the password is shown only if generated).
"""

from __future__ import annotations

import os
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from auth.passwords import hash_password

_KEYS = ("DASH_USER", "DASH_PASSWORD_HASH", "SESSION_SECRET")


def main() -> int:
    write = "--write" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    generated = False
    pw = os.environ.get("DASH_PW") or (args[0] if args else None)
    if not pw:
        pw = secrets.token_urlsafe(12)
        generated = True
    user = os.environ.get("DASH_USER_NAME", "owner")
    lines = [f"DASH_USER={user}", f"DASH_PASSWORD_HASH={hash_password(pw)}",
             f"SESSION_SECRET={secrets.token_hex(32)}"]

    if write:
        env = Path(".env")
        existing = env.read_text(encoding="utf-8").splitlines() if env.exists() else []
        keep = [ln for ln in existing if ln.split("=", 1)[0].strip() not in _KEYS]
        env.write_text("\n".join(keep + lines) + "\n", encoding="utf-8")
        print("CREDS_WRITTEN to .env (DASH_USER, DASH_PASSWORD_HASH, SESSION_SECRET)")
        if generated:
            print(f"# dashboard password (save it now): {pw}")
    else:
        print("# --- Add to .env ---")
        print("\n".join(lines))
        print(f"# dashboard password (save it): {pw}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
