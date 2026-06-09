"""Configuration loader.

Loads settings from two portable sources, with no third-party dependencies:

1. ``.env``  (local, gitignored) — secrets and environment overrides.
2. ``config/settings.json`` (or ``settings.example.json`` as fallback) — non-secret
   defaults that are safe to commit.

Environment variables always win over the JSON file. Secrets live ONLY in ``.env``;
never put them in ``settings.json``.

A minimal pure-Python ``.env`` parser is built in so the skeleton runs with the
standard library alone. (If ``python-dotenv`` is installed later, you may switch to it.)
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Optional

from core import paths


def load_dotenv(path=paths.ENV_FILE, *, override: bool = False) -> dict[str, str]:
    """Parse a ``.env`` file and populate ``os.environ``.

    - Ignores blank lines and ``#`` comments.
    - Supports ``KEY=value`` and ``export KEY=value``.
    - Strips matching surrounding single/double quotes.
    - By default does NOT override variables already set in the real environment.

    Returns the dict of values found in the file (whether or not they were applied).
    """
    found: dict[str, str] = {}
    if not path.exists():
        return found

    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export "):]
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if (len(value) >= 2) and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        found[key] = value
        if override or key not in os.environ:
            os.environ[key] = value
    return found


def _load_settings_json() -> dict[str, Any]:
    """Read settings.json, falling back to settings.example.json, falling back to {}."""
    for candidate in (paths.SETTINGS_FILE, paths.SETTINGS_EXAMPLE_FILE):
        if candidate.exists():
            try:
                return json.loads(candidate.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                # Malformed config should not crash startup; treat as empty.
                return {}
    return {}


@dataclass
class Config:
    """Resolved configuration. Read-only snapshot taken at load time."""

    env: str = "local"
    log_level: str = "info"
    settings: dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        """Look up a value: environment variable first, then settings.json, then default."""
        if key in os.environ:
            return os.environ[key]
        if key in self.settings:
            return self.settings[key]
        return default

    def secret(self, key: str) -> Optional[str]:
        """Fetch a secret from the environment only (never from the committed JSON)."""
        return os.environ.get(key)

    @property
    def is_local(self) -> bool:
        return self.env == "local"


def load_config() -> Config:
    """Load ``.env`` then build a :class:`Config`. Call this once at startup."""
    load_dotenv()
    settings = _load_settings_json()
    return Config(
        env=os.environ.get("SPORTSVERSE_ENV", settings.get("env", "local")),
        log_level=os.environ.get("LOG_LEVEL", settings.get("log_level", "info")),
        settings=settings,
    )
