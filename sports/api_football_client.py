"""API-Football client (api-sports.io direct API) — stdlib urllib only.

Auth: header ``x-apisports-key: <API_FOOTBALL_KEY>``. The key is read from ``.env`` only, used
server-side only, and NEVER logged or returned to the browser. Defensive like the ESPN client; the
Hub adds caching, health, and fallback on top.

Docs: https://www.api-football.com/documentation-v3
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Callable, Optional

API_FOOTBALL_BASE = "https://v3.football.api-sports.io"
_USER_AGENT = "SportsverseBot/1.0 (+https://sportsversenews.com)"


class APIFootballError(RuntimeError):
    """Raised when an API-Football request fails or returns an error payload."""


class APIFootballClient:
    """Read-only API-Football client. Inject ``fetch`` in tests to avoid network/secrets."""

    name = "API-Football"

    def __init__(self, api_key: Optional[str] = None,
                 fetch: Optional[Callable[[str, dict], dict]] = None) -> None:
        self._key = api_key
        self._fetch = fetch or self._default_fetch

    @property
    def configured(self) -> bool:
        return bool(self._key)

    def _default_fetch(self, path: str, params: dict) -> dict:
        if not self._key:
            raise APIFootballError("API_FOOTBALL_KEY not configured")
        url = f"{API_FOOTBALL_BASE}{path}"
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={
            "x-apisports-key": self._key,  # secret header; never logged
            "User-Agent": _USER_AGENT, "Accept": "application/json",
        })
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                if resp.status != 200:
                    raise APIFootballError(f"HTTP {resp.status} for {path}")
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            # Don't echo the URL (it never contains the key, but stay conservative).
            raise APIFootballError(f"HTTP {exc.code} for {path}") from exc
        except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
            raise APIFootballError(f"request failed for {path}: {type(exc).__name__}") from exc

    def _get(self, path: str, params: Optional[dict] = None) -> list:
        data = self._fetch(path, params or {})
        errors = data.get("errors")
        # API-Football returns errors as {} (none) or a populated dict/list.
        if errors and (isinstance(errors, dict) and errors or isinstance(errors, list) and errors):
            raise APIFootballError(f"API error: {errors}")
        return data.get("response", []) or []

    # ---- account / health ------------------------------------------- #
    def status(self) -> dict:
        resp = self._fetch("/status", {})
        r = (resp.get("response") or {})
        sub = r.get("subscription", {}) or {}
        req = r.get("requests", {}) or {}
        return {
            "account": (r.get("account", {}) or {}).get("email") or "ok",
            "plan": sub.get("plan"),
            "active": sub.get("active"),
            "requests_today": req.get("current"),
            "requests_limit": req.get("limit_day"),
        }

    # ---- normalized resources --------------------------------------- #
    @staticmethod
    def _norm_fixture(f: dict) -> dict:
        fx, lg = f.get("fixture", {}) or {}, f.get("league", {}) or {}
        teams, goals = f.get("teams", {}) or {}, f.get("goals", {}) or {}
        st = (fx.get("status", {}) or {})
        return {
            "league": lg.get("name"), "country": lg.get("country"), "round": lg.get("round"),
            "status": st.get("long"), "short": st.get("short"), "elapsed": st.get("elapsed"),
            "date": fx.get("date"),
            "home": (teams.get("home", {}) or {}).get("name"),
            "away": (teams.get("away", {}) or {}).get("name"),
            "score_home": goals.get("home"), "score_away": goals.get("away"),
        }

    def live_fixtures(self) -> list[dict]:
        return [self._norm_fixture(f) for f in self._get("/fixtures", {"live": "all"})]

    def fixtures_by_date(self, date: str) -> list[dict]:
        return [self._norm_fixture(f) for f in self._get("/fixtures", {"date": date})]

    def standings(self, league: int, season: int) -> list[dict]:
        resp = self._get("/standings", {"league": league, "season": season})
        out = []
        for entry in resp:
            for group in ((entry.get("league", {}) or {}).get("standings") or []):
                for t in group:
                    out.append({"rank": t.get("rank"), "team": (t.get("team", {}) or {}).get("name"),
                                "points": t.get("points"),
                                "played": (t.get("all", {}) or {}).get("played")})
        return out

    def injuries(self, league: int, season: int) -> list[dict]:
        resp = self._get("/injuries", {"league": league, "season": season})
        return [{"player": (i.get("player", {}) or {}).get("name"),
                 "team": (i.get("team", {}) or {}).get("name"),
                 "reason": (i.get("player", {}) or {}).get("reason")} for i in resp]

    def transfers(self, team: int) -> list[dict]:
        resp = self._get("/transfers", {"team": team})
        out = []
        for p in resp:
            for tr in (p.get("transfers") or []):
                out.append({"player": (p.get("player", {}) or {}).get("name"),
                            "date": tr.get("date"),
                            "from": (tr.get("teams", {}) or {}).get("out", {}).get("name"),
                            "to": (tr.get("teams", {}) or {}).get("in", {}).get("name")})
        return out
