"""Sports Data Hub tests — fully offline (injected fetch, temp DB/state)."""

import time

import pytest

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
