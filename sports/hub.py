"""SportsDataHub — the ONLY entry point agents use for sports data.

Flow:  caller -> Hub -> (cache hit? return) -> provider -> cache + health -> return.
On provider failure the Hub records health (which may alert via Telegram) and serves **stale**
cached data when available, so the dashboard/agents degrade gracefully instead of breaking.

Agents must never import ESPNClient / API-Football directly — always go through the Hub.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Callable, Optional

from sports.cache import SportsCache
from sports.espn_client import LEAGUES, ESPNClient, ESPNError
from sports.health import SportsApiHealthMonitor

DEFAULT_TTL = {"scoreboard": 60, "news": 600, "teams": 86400}
_CONFIG_FILE = Path("config") / "sports.json"


def _load_ttl() -> dict:
    ttl = dict(DEFAULT_TTL)
    if _CONFIG_FILE.exists():
        try:
            ttl.update((json.loads(_CONFIG_FILE.read_text(encoding="utf-8")) or {}).get("ttl_seconds", {}))
        except (ValueError, OSError):
            pass
    return ttl


def default_telegram_alert(config=None) -> Optional[Callable[[str], None]]:
    """Build a Telegram alert callback if the bot is configured, else None (no alerts)."""
    try:
        from core.config import load_config
        from integrations.telegram_bot import JarvisTelegramBot
        cfg = config or load_config()
        if not cfg.secret("TELEGRAM_BOT_TOKEN"):
            return None
        bot = JarvisTelegramBot(cfg)
        return lambda msg: bot.send(msg)
    except Exception:
        return None


class SportsDataHub:
    def __init__(self, config=None, cache: Optional[SportsCache] = None,
                 espn: Optional[ESPNClient] = None,
                 health: Optional[SportsApiHealthMonitor] = None,
                 alert: Optional[Callable[[str], None]] = None) -> None:
        self.config = config
        self.cache = cache or SportsCache()
        self.espn = espn or ESPNClient()
        self.health = health or SportsApiHealthMonitor(
            on_alert=alert if alert is not None else default_telegram_alert(config))
        self.ttl = _load_ttl()

    # ---- core read-through ------------------------------------------ #
    def _read(self, provider, method: str, key: str, ttl: float, *args) -> dict:
        cached = self.cache.get(key, ttl)
        if cached is not None:
            return {"ok": True, "data": cached, "cached": True, "stale": False,
                    "age": self.cache.age(key)}
        t0 = time.time()
        try:
            data = getattr(provider, method)(*args)
            self.health.record_ok(provider.name, (time.time() - t0) * 1000)
            self.cache.set(key, data)
            return {"ok": True, "data": data, "cached": False, "stale": False, "age": 0.0}
        except ESPNError as exc:
            self.health.record_failure(provider.name, str(exc))
            stale = self.cache.get_stale(key)
            if stale is not None:
                return {"ok": True, "data": stale["value"], "cached": True, "stale": True,
                        "age": stale["age"], "warning": f"{provider.name} unavailable; showing cached data"}
            return {"ok": False, "data": None, "error": str(exc), "provider": provider.name}

    # ---- ESPN-backed reads ------------------------------------------ #
    def scoreboard(self, league: str) -> dict:
        return self._read(self.espn, "scoreboard", f"espn:scoreboard:{league}", self.ttl["scoreboard"], league)

    def news(self, league: str, limit: int = 10) -> dict:
        return self._read(self.espn, "news", f"espn:news:{league}:{limit}", self.ttl["news"], league, limit)

    def teams(self, league: str) -> dict:
        return self._read(self.espn, "teams", f"espn:teams:{league}", self.ttl["teams"], league)

    # ---- aggregates -------------------------------------------------- #
    def _games_by_state(self, states: set[str], leagues: Optional[list[str]] = None) -> list[dict]:
        out = []
        for lg in (leagues or list(LEAGUES)):
            res = self.scoreboard(lg)
            if not res.get("ok"):
                continue
            for g in res["data"]:
                if g.get("state") in states:
                    out.append({**g, "league": lg})
        return out

    def live_games(self, leagues: Optional[list[str]] = None) -> list[dict]:
        return self._games_by_state({"in"}, leagues)

    def upcoming_games(self, leagues: Optional[list[str]] = None) -> list[dict]:
        return self._games_by_state({"pre"}, leagues)

    def latest_news(self, leagues: Optional[list[str]] = None, per_league: int = 3) -> list[dict]:
        out = []
        for lg in (leagues or list(LEAGUES)):
            res = self.news(lg, per_league)
            if res.get("ok"):
                out.extend({**n, "league": lg} for n in res["data"][:per_league])
        return out

    # ---- status for dashboard --------------------------------------- #
    def providers_status(self) -> dict:
        status = self.health.status()
        # ESPN may not have been called yet; show "unknown" rather than nothing.
        status.setdefault("ESPN", {"state": "unknown", "healthy": True, "last_ok": None,
                                    "last_error": None, "last_latency_ms": None,
                                    "consecutive_failures": 0, "total_calls": 0, "total_failures": 0})
        status.setdefault("API-Football", {"state": "needs API key", "healthy": True, "last_ok": None,
                                           "last_error": "API-Football key not configured", "last_latency_ms": None,
                                           "consecutive_failures": 0, "total_calls": 0, "total_failures": 0})
        return status
