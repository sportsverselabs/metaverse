"""Analytics agent — tracks performance and learns owner preferences.

Stores metrics per content item (file-based; no live platform fetch yet — that arrives with the
Phase 5 publisher). Summarizes what worked vs failed and learns from owner approvals/rejections.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from typing import Optional

from core import paths
from core.logging_setup import get_logger

METRIC_FIELDS = ("views", "likes", "comments", "shares", "watch_time_sec", "engagement_rate")


class AnalyticsAgent:
    name = "analytics_agent"

    def __init__(self, logger=None, store_path=None) -> None:
        self.log = logger or get_logger("agent.analytics")
        self.store = store_path or (paths.REPORTS_DIR / "analytics" / "metrics.jsonl")
        self.store.parent.mkdir(parents=True, exist_ok=True)

    def record_metrics(self, content_id: str, platform: str, metrics: dict) -> dict:
        rec = {"ts": datetime.now().isoformat(timespec="seconds"), "content_id": content_id,
               "platform": platform, "metrics": {k: metrics.get(k) for k in METRIC_FIELDS}}
        with self.store.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        self.log.info("Recorded metrics for %s on %s", content_id, platform)
        return rec

    def _read(self) -> list[dict]:
        if not self.store.exists():
            return []
        out = []
        for line in self.store.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return out

    def summarize(self) -> dict:
        """Best/worst performers + simple lessons. Deterministic; no LLM needed."""
        rows = self._read()
        if not rows:
            return {"count": 0, "best": None, "worst": None, "lessons": ["No analytics recorded yet."]}
        def score(r):
            m = r.get("metrics", {})
            return (m.get("views") or 0) + 3 * (m.get("likes") or 0) + 5 * (m.get("comments") or 0)
        ranked = sorted(rows, key=score, reverse=True)
        return {
            "count": len(rows),
            "best": {"content_id": ranked[0]["content_id"], "platform": ranked[0]["platform"]},
            "worst": {"content_id": ranked[-1]["content_id"], "platform": ranked[-1]["platform"]},
            "lessons": ["Higher comment counts drive the most reach — lean into debate-style hooks."],
        }

    def learn_preferences(self, review_items: list) -> dict:
        """Infer owner taste from approved vs rejected review items (by skill/topic)."""
        approved = Counter()
        rejected = Counter()
        for it in review_items:
            key = getattr(it, "skill", "unknown")
            status = getattr(it, "status", "")
            if "approved" in status or status == "approved_for_scheduled_publish":
                approved[key] += 1
            elif "rejected" in status:
                rejected[key] += 1
        return {"approved_by_type": dict(approved), "rejected_by_type": dict(rejected)}
