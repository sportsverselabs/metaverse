"""Owner-gated publishing service.

This is the only code path that may turn an approved review item into a real
platform post. Orchestration and scheduling still never publish.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from core import paths
from core.config import load_config
from core.logging_setup import get_logger
from publishing.base import PublishResult, Publisher
from publishing.instagram import InstagramPublisher
from publishing.tiktok import TikTokPublisher
from publishing.youtube import YouTubePublisher
from review.models import STATUS_OWNER_APPROVED, STATUS_PUBLISHED, STATUS_SCHEDULED, ReviewItem

PUBLISHABLE_STATUSES = frozenset({STATUS_OWNER_APPROVED, STATUS_SCHEDULED})


class PublishingService:
    def __init__(
        self,
        config=None,
        review_store=None,
        memory=None,
        publishers: Optional[dict[str, Publisher]] = None,
        posts_log: Optional[Path] = None,
        alert: Optional[Callable[[str], None]] = None,
        logger=None,
    ) -> None:
        self.config = config or load_config()
        self.review_store = review_store
        self.memory = memory
        self.log = logger or get_logger("publishing.service")
        self.publishers = publishers or {
            "youtube": YouTubePublisher(config=self.config),
            "instagram": InstagramPublisher(config=self.config),
            "tiktok": TikTokPublisher(config=self.config),
        }
        self.posts_log = posts_log or (paths.REPORTS_DIR / "posts" / "publish_log.jsonl")
        self.posts_log.parent.mkdir(parents=True, exist_ok=True)
        self.alert = alert if alert is not None else self._default_alert()

    def configured(self, platform: str) -> bool:
        publisher = self.publishers.get(platform.lower())
        return bool(publisher and publisher.configured)

    def connection_statuses(self) -> list[dict]:
        out = []
        for platform in ("youtube", "instagram", "tiktok"):
            publisher = self.publishers.get(platform)
            ok = bool(publisher and publisher.configured)
            out.append({
                "platform": platform,
                "configured": ok,
                "status": "connected" if ok else "needs owner setup",
            })
        return out

    def publish(self, post: dict, *, platform: str = "", approved: bool = False,
                visibility: str = "private") -> PublishResult:
        platform = (platform or post.get("platform") or "").strip().lower()
        if not approved:
            return PublishResult(False, platform or "unknown", reason="owner approval required before publishing")
        publisher = self.publishers.get(platform)
        if publisher is None:
            return PublishResult(False, platform or "unknown", reason="unsupported platform")
        try:
            result = publisher.publish(post, visibility=visibility)
        except Exception as exc:  # never raise platform failures into dashboard/review callers
            self.log.error("Publish failed for %s: %s", platform, type(exc).__name__)
            result = PublishResult(False, platform, reason=f"publish failed: {type(exc).__name__}")
        self._log_post(post, result, visibility=visibility)
        return result

    def publish_review_item(self, item_or_id, *, platform: str,
                            visibility: str = "private", by: str = "owner") -> PublishResult:
        item = self._resolve_item(item_or_id)
        platform = platform.strip().lower()
        if item.status not in PUBLISHABLE_STATUSES:
            return PublishResult(False, platform, reason="review item must be owner-approved or scheduled")

        post = self._post_from_item(item, platform)
        result = self.publish(post, platform=platform, approved=True, visibility=visibility)
        if result.ok:
            item.status = STATUS_PUBLISHED
            item.published = True
            item.published_at = datetime.now().isoformat(timespec="seconds")
            item.published_platform = platform
            item.post_id = result.post_id
            item.post_url = result.url
            item.add_history("published", by=by,
                             notes=f"{platform} {result.post_id or result.url or '(no id returned)'}")
            if self.review_store is not None:
                self.review_store.update(item)
            self._audit(item, "published", owner_decision=f"{platform}:{visibility}",
                        final_status=STATUS_PUBLISHED)
            self._alert(f"Published {item.id} to {platform}: {result.url or result.post_id}")
        else:
            item.add_history("publish_failed", by=by, notes=f"{platform}: {result.reason}")
            if self.review_store is not None:
                self.review_store.update(item)
            self._audit(item, "publish_failed", owner_decision=f"{platform}:{visibility}",
                        final_status=item.status)
            self._alert(f"Publish failed for {item.id} to {platform}: {result.reason}")
        return result

    def _resolve_item(self, item_or_id) -> ReviewItem:
        if isinstance(item_or_id, ReviewItem):
            return item_or_id
        if self.review_store is None:
            raise ValueError("review_store is required when publishing by id")
        item = self.review_store.get(str(item_or_id))
        if item is None:
            raise ValueError(f"review item '{item_or_id}' not found")
        return item

    @staticmethod
    def _post_from_item(item: ReviewItem, platform: str) -> dict:
        title = item.skill.replace("_", " ").strip().title() or "Sportsverse post"
        return {
            "review_id": item.id,
            "platform": platform,
            "title": title,
            "body": item.content,
            "hashtags": [],
        }

    def _log_post(self, post: dict, result: PublishResult, *, visibility: str) -> None:
        rec = {
            "ts": datetime.now().isoformat(timespec="seconds"),
            "review_id": post.get("review_id", ""),
            "platform": result.platform,
            "ok": result.ok,
            "post_id": result.post_id,
            "url": result.url,
            "reason": result.reason,
            "visibility": visibility,
            "dry_run": result.dry_run,
        }
        with self.posts_log.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    def _audit(self, item: ReviewItem, action: str, *, owner_decision: str, final_status: str) -> None:
        score = item.compliance.get("risk_score") if isinstance(item.compliance, dict) else None
        if self.memory is not None and hasattr(self.memory, "log_audit"):
            try:
                self.memory.log_audit(draft_id=item.id, action=action, agent="publishing",
                                      owner_decision=owner_decision, compliance_score=score,
                                      final_status=final_status)
            except Exception:
                self.log.debug("publish audit failed", exc_info=True)
        if self.memory is not None and hasattr(self.memory, "log_event"):
            try:
                self.memory.log_event(f"publishing_{action}", f"{item.id} -> {final_status} ({owner_decision})")
            except Exception:
                self.log.debug("publish event failed", exc_info=True)

    def _default_alert(self):
        try:
            from integrations.telegram_bot import JarvisTelegramBot

            bot = JarvisTelegramBot(config=self.config)
            return bot.send if bot.configured else None
        except Exception:
            return None

    def _alert(self, message: str) -> None:
        if not self.alert:
            return
        try:
            self.alert(message)
        except Exception:
            self.log.debug("publish alert failed", exc_info=True)
