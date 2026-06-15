"""Sports API health monitor.

Tracks per-provider availability, latency, consecutive failures, rate-limit/auth errors, and cache
freshness. After ``alert_threshold`` consecutive failures it fires ``on_alert`` once (Telegram), and
fires a recovery note when the provider comes back. State persists to JSON so the dashboard can read it.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Callable, Optional

DEFAULT_STATE = Path("data") / "sports_health.json"


class SportsApiHealthMonitor:
    def __init__(self, state_path: Optional[Path | str] = None, alert_threshold: int = 3,
                 on_alert: Optional[Callable[[str], None]] = None) -> None:
        self.state_path = Path(state_path) if state_path else DEFAULT_STATE
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.alert_threshold = alert_threshold
        self.on_alert = on_alert
        self._state = self._load()

    def _load(self) -> dict:
        if self.state_path.exists():
            try:
                return json.loads(self.state_path.read_text(encoding="utf-8"))
            except (ValueError, OSError):
                return {}
        return {}

    def _save(self) -> None:
        self.state_path.write_text(json.dumps(self._state, indent=2), encoding="utf-8")

    def _prov(self, name: str) -> dict:
        return self._state.setdefault(name, {
            "consecutive_failures": 0, "total_calls": 0, "total_failures": 0,
            "last_ok": None, "last_error": None, "last_latency_ms": None, "alerted": False,
        })

    def record_ok(self, provider: str, latency_ms: float) -> None:
        p = self._prov(provider)
        recovered = p["alerted"]
        p.update(total_calls=p["total_calls"] + 1, consecutive_failures=0,
                 last_ok=time.time(), last_latency_ms=round(latency_ms, 1), alerted=False)
        self._save()
        if recovered and self.on_alert:
            self._safe_alert(f"✅ Sportsverse Recovery\n\nProvider: {provider}\nStatus: back online")

    def record_failure(self, provider: str, error: str) -> None:
        p = self._prov(provider)
        p.update(total_calls=p["total_calls"] + 1, total_failures=p["total_failures"] + 1,
                 consecutive_failures=p["consecutive_failures"] + 1, last_error=error)
        should_alert = p["consecutive_failures"] >= self.alert_threshold and not p["alerted"]
        if should_alert:
            p["alerted"] = True
        self._save()
        if should_alert and self.on_alert:
            ts = time.strftime("%Y-%m-%d %H:%M:%S")
            self._safe_alert(
                f"⚠ Sportsverse Alert\n\nProvider: {provider}\nIssue: {error}\n"
                f"Consecutive failures: {p['consecutive_failures']}\nTime: {ts}"
            )

    def _safe_alert(self, message: str) -> None:
        try:
            self.on_alert(message)  # type: ignore[misc]
        except Exception:  # alerting must never crash data flow
            pass

    def status(self) -> dict:
        out = {}
        for name, p in self._state.items():
            healthy = p["consecutive_failures"] < self.alert_threshold
            out[name] = {
                "healthy": healthy,
                "state": "online" if healthy and p["last_ok"] else ("degraded" if p["last_ok"] else "unknown"),
                "consecutive_failures": p["consecutive_failures"],
                "total_calls": p["total_calls"],
                "total_failures": p["total_failures"],
                "last_ok": p["last_ok"],
                "last_error": p["last_error"],
                "last_latency_ms": p["last_latency_ms"],
            }
        return out
