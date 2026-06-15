"""ESPN client (unofficial, keyless) — stdlib urllib only.

ESPN's public site API needs no key but is **unofficial**: endpoints can change or disappear, so
every call is defensive (timeouts, try/except, normalization) and the Hub layers caching + fallback
on top. Never assume endpoint stability.

Friendly league name -> (sport, league path) used by ESPN's site API:
    https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/{resource}
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Callable, Optional

ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports"
_USER_AGENT = "SportsverseBot/1.0 (+https://sportsversenews.com)"

# Owner-requested launch leagues.
LEAGUES: dict[str, tuple[str, str]] = {
    "NFL": ("football", "nfl"),
    "NBA": ("basketball", "nba"),
    "MLB": ("baseball", "mlb"),
    "NHL": ("hockey", "nhl"),
    "MLS": ("soccer", "usa.1"),
    "Premier League": ("soccer", "eng.1"),
}


class ESPNError(RuntimeError):
    """Raised when an ESPN request fails or returns an unusable response."""


def _default_fetch(url: str, timeout: float = 12.0) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status != 200:
                raise ESPNError(f"HTTP {resp.status} for {url}")
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise ESPNError(f"HTTP {exc.code} for {url}") from exc
    except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
        raise ESPNError(f"request failed for {url}: {type(exc).__name__}") from exc


class ESPNClient:
    """Read-only ESPN client. Inject ``fetch`` in tests to avoid network."""

    name = "ESPN"

    def __init__(self, fetch: Optional[Callable[[str], dict]] = None) -> None:
        self._fetch = fetch or _default_fetch

    @staticmethod
    def _resolve(league: str) -> tuple[str, str]:
        if league not in LEAGUES:
            raise ESPNError(f"unknown league '{league}'. Known: {', '.join(LEAGUES)}")
        return LEAGUES[league]

    def _url(self, league: str, resource: str) -> str:
        sport, lpath = self._resolve(league)
        return f"{ESPN_BASE}/{sport}/{lpath}/{resource}"

    # ---- normalized resources --------------------------------------- #
    def scoreboard(self, league: str) -> list[dict]:
        data = self._fetch(self._url(league, "scoreboard"))
        games = []
        for ev in data.get("events", []) or []:
            comp = (ev.get("competitions") or [{}])[0]
            competitors = comp.get("competitors", []) or []
            def side(home: bool) -> dict:
                for c in competitors:
                    if (c.get("homeAway") == "home") == home:
                        return {"team": (c.get("team") or {}).get("displayName", "?"),
                                "score": c.get("score")}
                return {"team": "?", "score": None}
            status = (((ev.get("status") or {}).get("type") or {}).get("description")) or "scheduled"
            games.append({
                "name": ev.get("name", "?"),
                "short": ev.get("shortName", ""),
                "status": status,
                "state": (((ev.get("status") or {}).get("type") or {}).get("state")) or "pre",
                "start": ev.get("date"),
                "home": side(True),
                "away": side(False),
            })
        return games

    def news(self, league: str, limit: int = 10) -> list[dict]:
        data = self._fetch(self._url(league, "news"))
        items = []
        for a in (data.get("articles", []) or [])[:limit]:
            links = ((a.get("links") or {}).get("web") or {}).get("href")
            items.append({
                "headline": a.get("headline", "?"),
                "published": a.get("published"),
                "description": a.get("description", ""),
                "link": links,
            })
        return items

    def teams(self, league: str) -> list[dict]:
        data = self._fetch(self._url(league, "teams"))
        out = []
        groups = (((data.get("sports") or [{}])[0].get("leagues") or [{}])[0].get("teams")) or []
        for t in groups:
            team = t.get("team") or {}
            out.append({"name": team.get("displayName", "?"),
                        "abbreviation": team.get("abbreviation", ""),
                        "location": team.get("location", "")})
        return out
