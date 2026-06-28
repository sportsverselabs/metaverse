"""SportsContext — bridges the Sports Data Hub into Jarvis/Hermes and the worker agents.

Two jobs:
  1. **Direct answers** for pure factual questions ("what games are live?", "latest NBA news") —
     answered straight from the Hub with NO LLM call (no spend).
  2. **Grounding briefs** — a compact block of real live/upcoming/news data injected into a
     drafting prompt so Content/Research agents write from real scores instead of guessing.

Everything is best-effort: if the Hub or a provider is unavailable, methods return "" / [] and the
caller falls back to normal behavior. Never raises into the agent flow.
"""

from __future__ import annotations

from typing import Optional

from core.logging_setup import get_logger
from sports.espn_client import LEAGUES

_log = get_logger("sports.context")

# Words that signal the request is about sports at all.
_SPORT_WORDS = ("game", "games", "match", "matches", "score", "scores", "fixture", "standings",
                "injury", "injuries", "transfer", "playoff", "highlight", "sports")

# League aliases -> canonical league name used by the Hub/ESPN.
_LEAGUE_ALIASES = {
    "nfl": "NFL", "football nfl": "NFL",
    "nba": "NBA", "basketball": "NBA",
    "mlb": "MLB", "baseball": "MLB",
    "nhl": "NHL", "hockey": "NHL",
    "mls": "MLS",
    "premier league": "Premier League", "epl": "Premier League",
}

# Pure-data-question intents (answerable with no LLM).
_LIVE_INTENTS = ("what games are live", "live games", "live scores", "games live", "live now",
                 "what's the score", "whats the score", "what is the score", "scores right now",
                 "who's playing", "whos playing", "any games", "games today", "games on", "what games")
_NEWS_INTENTS = ("latest news", "any news", "sports news", "what's the news", "whats the news",
                 "headlines", "what happened")


class SportsContext:
    def __init__(self, hub=None, config=None) -> None:
        self._hub = hub
        self._config = config

    @property
    def hub(self):
        if self._hub is None:
            from core.config import load_config
            from sports.hub import SportsDataHub
            self._hub = SportsDataHub(config=self._config or load_config())
        return self._hub

    # ---- detection --------------------------------------------------- #
    @staticmethod
    def detect_leagues(text: str) -> list[str]:
        low = (text or "").lower()
        found = []
        for alias, name in _LEAGUE_ALIASES.items():
            if alias in low and name not in found:
                found.append(name)
        return found

    @classmethod
    def is_sports_related(cls, text: str) -> bool:
        low = (text or "").lower()
        return bool(cls.detect_leagues(text)) or any(w in low for w in _SPORT_WORDS) \
            or any(i in low for i in _LIVE_INTENTS + _NEWS_INTENTS)

    @classmethod
    def _news_query(cls, text: str) -> bool:
        low = (text or "").lower()
        if any(i in low for i in _NEWS_INTENTS):
            return True
        # "news" plus a sports signal ("latest NBA news", "NFL news", "sports news")
        return "news" in low and ("latest" in low or "sports" in low or bool(cls.detect_leagues(text)))

    @classmethod
    def is_data_query(cls, text: str) -> bool:
        """True only for short factual questions we can answer from the Hub without an LLM."""
        low = (text or "").lower()
        if any(i in low for i in _LIVE_INTENTS) or cls._news_query(text):
            return True
        # "scores"/"standings" as a near-standalone question
        if low.strip().rstrip("?").strip() in ("scores", "live", "standings", "news"):
            return True
        return False

    @classmethod
    def _intent(cls, text: str) -> str:
        return "news" if cls._news_query(text) or (text or "").lower().strip().rstrip("?").strip() == "news" else "live"

    # ---- direct answer (no LLM) ------------------------------------- #
    def direct_answer(self, text: str) -> str:
        leagues = self.detect_leagues(text) or None
        try:
            if self._intent(text) == "news":
                return self._format_news(self.hub.latest_news(leagues=leagues, per_league=3))
            return self._format_live(text, leagues)
        except Exception as exc:  # pragma: no cover - safety net
            _log.error("direct_answer failed: %s", type(exc).__name__)
            return "Sorry — I couldn't reach the sports data just now. Try again in a moment."

    def _format_live(self, text: str, leagues) -> str:
        live = self.hub.live_games(leagues)
        soccer = []
        if self.hub.football_configured() and (leagues is None or "Premier League" in (leagues or []) or "MLS" in (leagues or [])):
            res = self.hub.football_live()
            if res.get("ok"):
                soccer = res.get("data") or []
        lines = []
        if live:
            lines.append("Live now (ESPN):")
            lines += [f"  • [{g['league']}] {g['away']['team']} {g['away'].get('score') or 0}"
                      f" @ {g['home']['team']} {g['home'].get('score') or 0} — {g['status']}" for g in live[:12]]
        if soccer:
            lines.append("Live soccer (API-Football):")
            lines += [f"  • [{g.get('league')}] {g.get('home')} {g.get('score_home')}"
                      f"–{g.get('score_away')} {g.get('away')} ({g.get('elapsed')}')" for g in soccer[:8]]
        if not lines:
            up = self.hub.upcoming_games(leagues)[:6]
            if up:
                lines.append("No games live right now. Upcoming:")
                lines += [f"  • [{g['league']}] {g['short'] or g['name']} — {g.get('start','')}" for g in up]
            else:
                lines.append("No live or upcoming games found right now.")
        return "\n".join(lines)

    def _format_news(self, items) -> str:
        if not items:
            return "No sports headlines available right now."
        lines = ["Latest sports headlines:"]
        lines += [f"  • [{n.get('league','')}] {n.get('headline')}" for n in items[:12]]
        return "\n".join(lines)

    # ---- grounding brief for drafting ------------------------------- #
    def brief(self, text: str, max_news: int = 5) -> str:
        """Compact real-data block to prepend to a drafting prompt. '' if not sports-related."""
        if not self.is_sports_related(text):
            return ""
        leagues = self.detect_leagues(text) or None
        try:
            live = self.hub.live_games(leagues)
            upcoming = self.hub.upcoming_games(leagues)[:5]
            news = self.hub.latest_news(leagues=leagues, per_league=2)[:max_news]
        except Exception as exc:  # pragma: no cover - safety net
            _log.error("brief failed: %s", type(exc).__name__)
            return ""
        if not (live or upcoming or news):
            return ""
        parts = ["REAL-TIME SPORTS DATA (use these facts; do not invent scores or games):"]
        if live:
            parts.append("Live: " + "; ".join(
                f"[{g['league']}] {g['away']['team']} {g['away'].get('score') or 0}-"
                f"{g['home'].get('score') or 0} {g['home']['team']} ({g['status']})" for g in live[:8]))
        if upcoming:
            parts.append("Upcoming: " + "; ".join(f"[{g['league']}] {g['short'] or g['name']}" for g in upcoming))
        if news:
            parts.append("Headlines: " + "; ".join(f"[{n.get('league','')}] {n.get('headline')}" for n in news))
        return "\n".join(parts)
