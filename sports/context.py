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

# Sport aliases -> canonical sport, and the ESPN leagues that cover that sport.
_SPORT_ALIASES = {
    "soccer": "soccer", "futbol": "soccer", "epl": "soccer", "premier league": "soccer",
    "la liga": "soccer", "champions league": "soccer", "ucl": "soccer", "mls": "soccer",
    "nfl": "nfl", "nba": "nba", "basketball": "nba", "mlb": "mlb", "baseball": "mlb",
    "nhl": "nhl", "hockey": "nhl",
}
_SPORT_TO_LEAGUES = {
    "soccer": ["Premier League", "MLS"],
    "nfl": ["NFL"], "nba": ["NBA"], "mlb": ["MLB"], "nhl": ["NHL"],
}

# Source-basis labels every generated idea must carry.
BASIS_LIVE = "live-data"
BASIS_NEWS = "recent-news"
BASIS_TREND = "trending-topic"
BASIS_EVERGREEN = "evergreen"
_VALID_BASIS = {BASIS_LIVE, BASIS_NEWS, BASIS_TREND, BASIS_EVERGREEN}

# Requests that want CONTENT IDEAS (vs a factual data answer).
_IDEA_WORDS = ("idea", "ideas", "highlight", "highlights", "video", "videos", "content",
               "brainstorm", "concept", "concepts", "make me", "script", "reel", "short")

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

    @staticmethod
    def detect_sport(text: str) -> Optional[str]:
        """Return a canonical sport ('soccer'/'nfl'/'nba'/'mlb'/'nhl') if the text names one."""
        low = (text or "").lower()
        for alias, sport in _SPORT_ALIASES.items():
            if alias in low:
                return sport
        return None

    @classmethod
    def sport_scope(cls, text: str):
        """(sport, leagues, scope_label) for the requested sport, or (None, None, 'sports')."""
        sport = cls.detect_sport(text)
        leagues = _SPORT_TO_LEAGUES.get(sport) if sport else (cls.detect_leagues(text) or None)
        if leagues and len(leagues) == 1:
            scope = leagues[0]
        elif sport:
            scope = sport
        else:
            scope = "sports"
        return sport, leagues, scope

    @staticmethod
    def _wants_ideas(text: str) -> bool:
        low = (text or "").lower()
        return any(w in low for w in _IDEA_WORDS)

    @classmethod
    def is_sports_related(cls, text: str) -> bool:
        low = (text or "").lower()
        return bool(cls.detect_leagues(text)) or bool(cls.detect_sport(text)) \
            or any(w in low for w in _SPORT_WORDS) \
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

    # ---- research basis + fallback idea generation ------------------ #
    def research_basis(self, text: str) -> dict:
        """Gather everything available for the requested sport, in preference order.

        Preference: live > recent results > news > trending > evergreen. Live/recent carry REAL
        scores from the Hub; trending/evergreen carry NO scores or events (so nothing is invented).
        """
        sport, leagues, scope = self.sport_scope(text)
        try:
            live = self.hub.live_games(leagues)
            upcoming = self.hub.upcoming_games(leagues)[:6]
            completed = self.hub.completed_games(leagues)[:6]
            news = self.hub.latest_news(leagues=leagues, per_league=3)[:8]
        except Exception as exc:  # pragma: no cover - safety net
            _log.error("research_basis failed: %s", type(exc).__name__)
            live = upcoming = completed = news = []
        soccer_live = []
        if sport == "soccer":
            try:
                if self.hub.football_configured():
                    r = self.hub.football_live()
                    if r.get("ok"):
                        soccer_live = (r.get("data") or [])[:6]
            except Exception:
                soccer_live = []
        return {"sport": sport, "leagues": leagues, "scope": scope,
                "live": live, "soccer_live": soccer_live, "upcoming": upcoming,
                "completed": completed, "news": news,
                "trending": self._trending_seeds(scope),
                "evergreen": self._evergreen_concepts(sport, scope)}

    @staticmethod
    def _trending_seeds(scope: str) -> list[str]:
        # Research ANGLES (topics to explore), not factual claims — no scores/events invented.
        return [f"Biggest {scope} storylines this season",
                f"Rising {scope} stars worth watching"]

    @staticmethod
    def _evergreen_concepts(sport, scope: str) -> list:
        # Timeless concepts — no specific score, quote, or event. Safe with zero live data.
        if sport == "soccer":
            base = [f"Top 10 greatest {scope} goals of all time",
                    f"Most iconic {scope} comebacks ever",
                    f"Legendary {scope} rivalries explained",
                    f"Best free-kick goals in {scope} history",
                    f"How {scope} tactics evolved over the decades"]
        else:
            s = scope if scope != "sports" else "sports"
            base = [f"Greatest {s} plays of all time",
                    f"Most clutch {s} moments ever",
                    f"Best {s} highlight compilation concepts",
                    f"Iconic {s} rivalries explained",
                    f"How {s} changed over the decades"]
        return [(t, "Timeless highlight reel — no current scores needed.") for t in base]

    def highlight_ideas(self, text: str, n: int = 3) -> list[dict]:
        """Return up to ``n`` sport-correct video ideas, each tagged with its source BASIS.

        Falls through live -> upcoming -> recent results -> news -> trending -> evergreen, so a sport
        with no live games STILL yields usable ideas. Never invents scores/quotes/events.
        """
        rb = self.research_basis(text)
        ideas: list[dict] = []

        for g in rb["live"]:
            ideas.append({"title": f"{g['away']['team']} vs {g['home']['team']} — live highlights",
                          "angle": f"Best moments from the live {g['league']} match.", "basis": BASIS_LIVE,
                          "source": (f"live {g['league']}: {g['away']['team']} {g['away'].get('score') or 0}-"
                                     f"{g['home'].get('score') or 0} {g['home']['team']} ({g['status']})")})
        for g in rb["soccer_live"]:
            ideas.append({"title": f"{g.get('home')} vs {g.get('away')} — live soccer highlights",
                          "angle": "Key chances and goals from the live match.", "basis": BASIS_LIVE,
                          "source": (f"live (API-Football): {g.get('home')} {g.get('score_home')}-"
                                     f"{g.get('score_away')} {g.get('away')} ({g.get('elapsed')}')")})
        for g in rb["upcoming"]:
            label = g.get("short") or g.get("name")
            ideas.append({"title": f"{label} — match preview", "basis": BASIS_LIVE,
                          "angle": "Storylines and what to watch ahead of the fixture.",
                          "source": f"upcoming {g.get('league')}: {label} ({g.get('start','')})"})
        for g in rb["completed"]:
            ideas.append({"title": f"{g['away']['team']} vs {g['home']['team']} — full-time recap",
                          "angle": "Turning points from the completed match.", "basis": BASIS_NEWS,
                          "source": (f"final {g['league']}: {g['away']['team']} {g['away'].get('score') or 0}-"
                                     f"{g['home'].get('score') or 0} {g['home']['team']}")})
        for h in rb["news"]:
            ideas.append({"title": f"{h.get('headline')} — explained", "basis": BASIS_NEWS,
                          "angle": "Break down the story for fans (verify before claiming specifics).",
                          "source": f"headline [{h.get('league','')}]: {h.get('headline')}"})
        for t in rb["trending"]:
            ideas.append({"title": t, "angle": "Trending-topic explainer.", "basis": BASIS_TREND,
                          "source": "trending research angle (no live data)"})
        for title, angle in rb["evergreen"]:
            ideas.append({"title": title, "angle": angle, "basis": BASIS_EVERGREEN,
                          "source": "evergreen concept (no specific event or score)"})
        return ideas[:n]

    # ---- grounding brief for drafting ------------------------------- #
    def brief(self, text: str, max_news: int = 5) -> str:
        """Real-data + fallback block to prepend to a drafting prompt. '' if not sports-related.

        For idea/highlight requests this ALWAYS returns usable, basis-labeled starting points
        (even with zero live games), and instructs the model never to invent scores or events.
        """
        if not self.is_sports_related(text):
            return ""
        try:
            if self._wants_ideas(text):
                return self._ideas_brief(text)
            return self._data_brief(text, max_news)
        except Exception as exc:  # pragma: no cover - safety net
            _log.error("brief failed: %s", type(exc).__name__)
            return ""

    def _ideas_brief(self, text: str) -> str:
        sport, _leagues, scope = self.sport_scope(text)
        ideas = self.highlight_ideas(text, n=3)
        if not ideas:
            return ""
        header = (f"GROUNDED {scope.upper()} HIGHLIGHT IDEAS — expand each into a usable video idea "
                  "(title, hook, 3-5 shot beats, CTA). KEEP each idea's BASIS tag. Preference used: "
                  "live data > recent results/news > trending > evergreen. "
                  "Do NOT invent scores, quotes, players, or events beyond the source shown.")
        lines = [header]
        for i, idea in enumerate(ideas, 1):
            lines.append(f"{i}. [{idea['basis']}] {idea['title']} — {idea['angle']} "
                         f"(source: {idea['source']})")
        return "\n".join(lines)

    def _data_brief(self, text: str, max_news: int) -> str:
        leagues = self.sport_scope(text)[1]
        live = self.hub.live_games(leagues)
        upcoming = self.hub.upcoming_games(leagues)[:5]
        news = self.hub.latest_news(leagues=leagues, per_league=2)[:max_news]
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
