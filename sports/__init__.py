"""Sportsverse Sports Data layer.

Central architecture: ESPN + API-Football -> SportsDataHub -> cache (SQLite) -> Hermes/Dashboard.
Agents must use ``SportsDataHub`` only; they never call the provider APIs directly.
"""

from sports.cache import SportsCache
from sports.espn_client import ESPNClient, ESPNError, LEAGUES
from sports.health import SportsApiHealthMonitor
from sports.hub import SportsDataHub

__all__ = [
    "SportsCache", "ESPNClient", "ESPNError", "LEAGUES",
    "SportsApiHealthMonitor", "SportsDataHub",
]
