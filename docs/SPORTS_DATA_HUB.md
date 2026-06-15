# Sports Data Hub

Central sports-data architecture for Sportsverse. **Agents never call ESPN or API-Football directly** —
they go through the Hub, which adds caching, health monitoring, graceful fallback, and Telegram alerts.

```
ESPN (keyless)         ┐
API-Football (key)     ┘──►  SportsDataHub  ──►  SQLite cache  ──►  Hermes / Dashboard / Content / Video
                              │
                              └──►  SportsApiHealthMonitor  ──►  Telegram alerts (on repeated failure)
```

## Components (in `sports/`)

| File | Role |
|------|------|
| `espn_client.py` | Read-only ESPN client (unofficial, keyless). Normalizes scoreboard / news / teams. Defensive — ESPN endpoints are not guaranteed stable. |
| `api_football_client.py` | *(not built yet — needs `API_FOOTBALL_KEY`)* fixtures/live/standings/players/injuries/transfers. |
| `cache.py` | `SportsCache` — SQLite TTL cache. Stores JSON; can return **stale** data on demand. |
| `health.py` | `SportsApiHealthMonitor` — tracks availability/latency/consecutive failures; alerts via Telegram after 3 failures; sends a recovery note when back. State persisted to `data/sports_health.json`. |
| `hub.py` | `SportsDataHub` — the single entry point. Read-through cache; serves stale data when a provider is down; records health. |

## How a read works

1. Caller asks the Hub (e.g. `hub.scoreboard("NBA")`).
2. **Cache hit** (within TTL) → return cached data immediately.
3. **Cache miss** → call the provider:
   - success → record health OK, cache the result, return it;
   - failure → record health failure (may fire a Telegram alert), and **return stale cache** if available
     (flagged `stale: true`), else return an error.

Every Hub result is a dict: `{ok, data, cached, stale, age, [warning|error]}`.

## Configuration

- `config/sports.json` — launch leagues, cache TTLs (`scoreboard` 60s, `news` 600s, `teams` 86400s),
  alert threshold (3 consecutive failures).
- `.env` — `API_FOOTBALL_KEY` (server-side only; never browser/logs). ESPN needs no key.

## Leagues at launch
NFL, NBA, MLB, NHL, MLS, Premier League (`sports/espn_client.py:LEAGUES`).

## Telegram alerts
Fired by the health monitor on: a provider failing `alert_threshold` times in a row, and on recovery.
Format:
```
⚠ Sportsverse Alert

Provider: ESPN
Issue: <error>
Consecutive failures: 3
Time: <timestamp>
```

## Dashboard
The **Sports Data** section shows provider health (state, latency, failure counts), live games, upcoming
games, and latest news, with a **Manual refresh** button. **Home** shows ESPN + API-Football status rows.

## Tests
`tests/test_sports.py` — fully offline (injected fetch, temp DB/state): cache TTL, ESPN normalization,
Hub read-through, stale-fallback on failure, and the 3-failure alert + recovery.

## Status
- ✅ ESPN client, cache, health monitor, Hub, Telegram alerts, dashboard Sports Data page — built & tested.
- ⏳ API-Football client — pending `API_FOOTBALL_KEY` from the owner.
- ⏳ IP-allowlist automation (restrict API-Football to the VPS IP) — pending paid plan.
