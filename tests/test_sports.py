"""Sports Data Hub tests — fully offline (injected fetch, temp DB/state)."""

import time

import pytest

from sports.api_football_client import APIFootballClient, APIFootballError
from sports.cache import SportsCache
from sports.espn_client import ESPNClient, ESPNError
from sports.health import SportsApiHealthMonitor
from sports.hub import SportsDataHub

# ---- sample ESPN payloads (trimmed) ---------------------------------- #
_SCOREBOARD = {
    "events": [{
        "name": "Team A at Team B", "shortName": "A @ B", "date": "2026-06-15T20:00Z",
        "status": {"type": {"description": "In Progress", "state": "in"}},
        "competitions": [{"competitors": [
            {"homeAway": "home", "team": {"displayName": "Team B"}, "score": "3"},
            {"homeAway": "away", "team": {"displayName": "Team A"}, "score": "1"},
        ]}],
    }]
}
_NEWS = {"articles": [{"headline": "Big trade", "published": "2026-06-15T10:00Z",
                       "description": "desc", "links": {"web": {"href": "http://x"}}}]}


def _fetch_factory(payload, fail=False):
    def _fetch(url):
        if fail:
            raise ESPNError("simulated outage")
        return payload
    return _fetch


def test_cache_ttl(tmp_path):
    c = SportsCache(tmp_path / "c.db")
    c.set("k", {"v": 1})
    assert c.get("k", ttl=100) == {"v": 1}
    assert c.get("k", ttl=0) is None          # expired by TTL
    assert c.get_stale("k")["value"] == {"v": 1}  # still retrievable as stale
    assert c.get("missing", ttl=100) is None


def test_espn_scoreboard_normalization():
    client = ESPNClient(fetch=_fetch_factory(_SCOREBOARD))
    games = client.scoreboard("NBA")
    assert games[0]["home"]["team"] == "Team B" and games[0]["home"]["score"] == "3"
    assert games[0]["away"]["team"] == "Team A"
    assert games[0]["state"] == "in"


def test_espn_unknown_league_raises():
    with pytest.raises(ESPNError):
        ESPNClient(fetch=_fetch_factory(_SCOREBOARD)).scoreboard("Cricket")


def test_hub_read_through_and_cache(tmp_path):
    hub = SportsDataHub(
        cache=SportsCache(tmp_path / "c.db"),
        espn=ESPNClient(fetch=_fetch_factory(_SCOREBOARD)),
        health=SportsApiHealthMonitor(state_path=tmp_path / "h.json"),
    )
    first = hub.scoreboard("NBA")
    assert first["ok"] and first["cached"] is False
    second = hub.scoreboard("NBA")
    assert second["cached"] is True  # served from cache


def test_hub_serves_stale_on_failure(tmp_path):
    cache = SportsCache(tmp_path / "c.db")
    health = SportsApiHealthMonitor(state_path=tmp_path / "h.json")
    ok_hub = SportsDataHub(cache=cache, espn=ESPNClient(fetch=_fetch_factory(_SCOREBOARD)), health=health)
    ok_hub.scoreboard("NBA")  # warm the cache
    # New hub whose provider is down; TTL forced to 0 so it must hit the provider (which fails).
    down_hub = SportsDataHub(cache=cache, espn=ESPNClient(fetch=_fetch_factory(None, fail=True)), health=health)
    down_hub.ttl["scoreboard"] = 0
    res = down_hub.scoreboard("NBA")
    assert res["ok"] and res["stale"] is True and "unavailable" in res["warning"]


def _offline_hub(tmp_path, football=True):
    return SportsDataHub(
        cache=SportsCache(tmp_path / "c.db"),
        espn=ESPNClient(fetch=lambda url: _SCOREBOARD),
        football=APIFootballClient(api_key="x", fetch=lambda p, par: _AF_LIVE) if football else None,
        health=SportsApiHealthMonitor(state_path=tmp_path / "h.json"),
    )


def test_context_query_detection_and_leagues():
    from sports.context import SportsContext
    assert SportsContext.is_data_query("what games are live?")
    assert SportsContext.is_data_query("latest NBA news")
    assert not SportsContext.is_data_query("draft 3 video ideas about the NBA finals")
    assert set(SportsContext.detect_leagues("latest NBA and NFL news")) == {"NFL", "NBA"}
    assert SportsContext.is_sports_related("write a caption for tonight's game")
    assert not SportsContext.is_sports_related("write a poem about cats")


def test_context_direct_answer(tmp_path):
    from sports.context import SportsContext
    sc = SportsContext(hub=_offline_hub(tmp_path))
    ans = sc.direct_answer("what games are live?")
    assert "Live" in ans and "Team A" in ans  # real game from the stub
    news = sc.direct_answer("latest news")
    assert "headlines" in news.lower()


def test_context_brief_only_when_sports(tmp_path):
    from sports.context import SportsContext
    sc = SportsContext(hub=_offline_hub(tmp_path))
    brief = sc.brief("draft a post about the NBA game tonight")
    assert "REAL-TIME SPORTS DATA" in brief
    assert sc.brief("write a poem about cats") == ""


def test_orchestration_fast_path_answers_without_llm(tmp_path):
    from types import SimpleNamespace
    from orchestration.journal import AgentJournal
    from orchestration.langgraph_app import _maybe_answer_sports
    from orchestration.state import OrchestrationState
    from sports.context import SportsContext
    sc = SportsContext(hub=_offline_hub(tmp_path))
    ctx = SimpleNamespace(extras={"sports_context": sc}, journal=AgentJournal(tmp_path / "j.jsonl"))
    state = OrchestrationState(user_request="what games are live?")
    out = _maybe_answer_sports(state, ctx)
    assert out is not None
    assert out.final_status == "answered_from_sports_hub"
    assert out.model_provider == ""           # no LLM/spend
    assert "sports_data_hub" in out.tools_used
    # A drafting request must NOT be short-circuited.
    assert _maybe_answer_sports(OrchestrationState(user_request="draft a video script about the NBA"), ctx) is None


_AF_LIVE = {"errors": [], "response": [{
    "fixture": {"date": "2026-06-15T20:00Z", "status": {"long": "Second Half", "short": "2H", "elapsed": 67}},
    "league": {"name": "Premier League", "country": "England"},
    "teams": {"home": {"name": "Arsenal"}, "away": {"name": "Chelsea"}},
    "goals": {"home": 2, "away": 1},
}]}
_AF_ERROR = {"errors": {"token": "invalid key"}, "response": []}


def test_api_football_normalization_and_error():
    client = APIFootballClient(api_key="x", fetch=lambda path, params: _AF_LIVE)
    games = client.live_fixtures()
    assert games[0]["home"] == "Arsenal" and games[0]["score_home"] == 2
    assert games[0]["league"] == "Premier League" and games[0]["elapsed"] == 67
    bad = APIFootballClient(api_key="x", fetch=lambda path, params: _AF_ERROR)
    with pytest.raises(APIFootballError):
        bad.live_fixtures()


def test_api_football_requires_key():
    assert APIFootballClient(api_key=None).configured is False
    with pytest.raises(APIFootballError):
        APIFootballClient(api_key=None).live_fixtures()


def test_hub_football_live_via_injected_client(tmp_path):
    client = APIFootballClient(api_key="x", fetch=lambda path, params: _AF_LIVE)
    hub = SportsDataHub(
        cache=SportsCache(tmp_path / "c.db"),
        espn=ESPNClient(fetch=lambda url: {"events": []}),
        football=client,
        health=SportsApiHealthMonitor(state_path=tmp_path / "h.json"),
    )
    assert hub.football_configured() is True
    res = hub.football_live()
    assert res["ok"] and res["data"][0]["home"] == "Arsenal"
    assert "API-Football" in hub.providers_status()


def test_hub_without_football_key(tmp_path):
    hub = SportsDataHub(
        cache=SportsCache(tmp_path / "c.db"),
        espn=ESPNClient(fetch=lambda url: {"events": []}),
        health=SportsApiHealthMonitor(state_path=tmp_path / "h.json"),
    )
    assert hub.football_configured() is False
    assert hub.football_live()["ok"] is False
    assert hub.providers_status()["API-Football"]["state"] == "needs API key"


def _empty_hub(tmp_path):
    """Hub with NO live/upcoming/completed games and NO news (worst case for fallback)."""
    empty = {"events": [], "articles": []}
    return SportsDataHub(
        cache=SportsCache(tmp_path / "c.db"),
        espn=ESPNClient(fetch=lambda url: empty),
        football=APIFootballClient(api_key="x", fetch=lambda p, par: {"errors": [], "response": []}),
        health=SportsApiHealthMonitor(state_path=tmp_path / "h.json"),
    )


def test_soccer_ideas_without_live_data_still_returns_three(tmp_path):
    from sports.context import SportsContext, _VALID_BASIS
    sc = SportsContext(hub=_empty_hub(tmp_path))
    ideas = sc.highlight_ideas("make me 3 soccer video highlights", n=3)
    assert len(ideas) == 3
    assert all(i["basis"] in _VALID_BASIS for i in ideas)          # every idea marks its source basis
    blob = " ".join(i["title"] + " " + i["angle"] for i in ideas).lower()
    assert "soccer" in blob                                         # sport-correct (not MLB/NFL)


def test_soccer_ideas_do_not_invent_scores(tmp_path):
    import re
    from sports.context import SportsContext
    sc = SportsContext(hub=_empty_hub(tmp_path))
    ideas = sc.highlight_ideas("3 soccer highlight videos", n=3)
    blob = " ".join(i["title"] + " " + i["angle"] + " " + i["source"] for i in ideas)
    assert not re.search(r"\d+\s*[-–]\s*\d+", blob)            # no fabricated "2-1" scores


def test_soccer_ideas_brief_marks_basis_and_forbids_invention(tmp_path):
    from sports.context import SportsContext
    sc = SportsContext(hub=_empty_hub(tmp_path))
    brief = sc.brief("make me 3 soccer video highlights")
    assert brief and "BASIS" in brief.upper()
    assert "1." in brief and "2." in brief and "3." in brief        # 3 ideas
    assert "trending-topic" in brief and "evergreen" in brief       # fallback tiers labeled
    assert "do not invent" in brief.lower()


def test_live_data_preferred_when_available(tmp_path):
    from sports.context import SportsContext, BASIS_LIVE
    sc = SportsContext(hub=_offline_hub(tmp_path))                  # _SCOREBOARD has an in-progress game
    ideas = sc.highlight_ideas("3 soccer highlights", n=3)
    assert ideas[0]["basis"] == BASIS_LIVE                          # live preferred over fallback


def test_soccer_request_routes_through_gated_content_path():
    # A highlight request is NOT a data query, so it flows through the content agent + compliance gate
    # (not the no-LLM fast path) — compliance runs and nothing publishes (gate proven in test_phase4_graph).
    from sports.context import SportsContext
    req = "make me 3 soccer video highlights"
    assert SportsContext.is_sports_related(req)
    assert SportsContext.detect_sport(req) == "soccer"
    assert SportsContext.is_data_query(req) is False


def test_health_alerts_after_three_failures(tmp_path):
    alerts = []
    mon = SportsApiHealthMonitor(state_path=tmp_path / "h.json", alert_threshold=3,
                                 on_alert=alerts.append)
    for _ in range(2):
        mon.record_failure("ESPN", "down")
    assert alerts == []            # not yet
    mon.record_failure("ESPN", "down")
    assert len(alerts) == 1 and "ESPN" in alerts[0]   # alert on the 3rd
    mon.record_failure("ESPN", "down")
    assert len(alerts) == 1        # no duplicate spam
    mon.record_ok("ESPN", 12.3)
    assert len(alerts) == 2 and "Recovery" in alerts[1]  # recovery note
