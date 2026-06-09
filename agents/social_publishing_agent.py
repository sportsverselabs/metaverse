"""Social publishing agent — PREPARES platform posts. It does NOT post.

Formats approved content for YouTube / Instagram / TikTok / website and logs what it prepared.
Actual posting requires (a) explicit owner approval AND (b) a Phase 5 platform-API capability
that does not exist yet. ``publish()`` always refuses unless both are present.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

from core import paths
from core.logging_setup import get_logger

PLATFORMS = ("youtube", "instagram", "tiktok", "website", "email")


class SocialPublishingAgent:
    name = "social_publishing_agent"

    def __init__(self, logger=None, posts_log=None) -> None:
        self.log = logger or get_logger("agent.social_publishing")
        self.posts_log = posts_log or (paths.REPORTS_DIR / "posts" / "posts_log.jsonl")
        self.posts_log.parent.mkdir(parents=True, exist_ok=True)

    def prepare(self, content: str, platform: str, *, title: str = "", hashtags: Optional[list] = None) -> dict:
        """Format a post for a platform. Returns a prepared (NOT posted) package."""
        platform = platform.lower()
        post = {
            "platform": platform,
            "title": title,
            "body": content,
            "hashtags": hashtags or [],
            "status": "prepared",      # never "posted" here
            "prepared_at": datetime.now().isoformat(timespec="seconds"),
        }
        self._log(post, "prepared")
        self.log.info("Prepared post for %s (not posted).", platform)
        return post

    def publish(self, post: dict, *, approved: bool = False, live_capability: bool = False) -> dict:
        """Refuses to post unless explicitly approved AND a live capability exists (Phase 5)."""
        if not approved:
            self._log(post, "blocked_no_approval")
            return {"status": "not_published", "reason": "owner approval required before publishing"}
        if not live_capability:
            self._log(post, "blocked_no_capability")
            return {"status": "not_published",
                    "reason": "live publishing is Phase 5 (owner-gated); no platform API is connected yet"}
        # Phase 5 would dispatch to the platform API here, per-item, after final confirmation.
        return {"status": "not_published", "reason": "publishing executor not implemented (Phase 5)"}

    def _log(self, post: dict, action: str) -> None:
        rec = {"ts": datetime.now().isoformat(timespec="seconds"), "action": action,
               "platform": post.get("platform"), "title": post.get("title", "")}
        with self.posts_log.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
