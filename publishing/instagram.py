"""Instagram Graph API publisher.

Instagram does not offer a universal private/draft publish mode through this
endpoint, so public publishing is guarded by IG_ALLOW_PUBLIC_PUBLISH. Use this
adapter first with an owner-controlled test account/app review setup.
"""

from __future__ import annotations

from typing import Callable, Optional

from publishing.base import PublishResult
from publishing.http import HttpResponse, default_fetch, form_body


class InstagramPublisher:
    platform = "instagram"

    def __init__(self, config=None,
                 fetch: Optional[Callable[..., HttpResponse]] = None) -> None:
        self.config = config
        self._fetch = fetch or default_fetch
        self._token = config.secret("IG_ACCESS_TOKEN") if config else None
        self._business_id = config.secret("IG_BUSINESS_ID") if config else None
        self._graph_version = (config.get("META_GRAPH_VERSION", "v23.0") or "v23.0") if config else "v23.0"
        self._allow_public = _truthy(config.get("IG_ALLOW_PUBLIC_PUBLISH", "false")) if config else False

    @property
    def configured(self) -> bool:
        return bool(self._token and self._business_id)

    def publish(self, post: dict, *, visibility: str = "private") -> PublishResult:
        if not self.configured:
            return PublishResult(False, self.platform, reason="Instagram not configured")
        if visibility not in {"public", "test"}:
            return PublishResult(False, self.platform,
                                 reason="Instagram API has no private/draft mode; use test/public with owner approval")
        if visibility == "public" and not self._allow_public:
            return PublishResult(False, self.platform, reason="Instagram public publishing disabled")

        media_url = str(post.get("media_url") or post.get("video_url") or post.get("image_url") or "").strip()
        if not media_url:
            return PublishResult(False, self.platform, reason="Instagram publishing requires a public media_url")

        is_video = bool(post.get("video_url") or post.get("is_video") or _looks_like_video(media_url))
        create_payload = {
            "access_token": self._token,
            "caption": _caption(post),
        }
        if is_video:
            create_payload.update({"media_type": post.get("media_type") or "REELS", "video_url": media_url})
        else:
            create_payload["image_url"] = media_url

        create = self._fetch(
            "POST",
            self._url("media"),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            body=form_body(create_payload),
        )
        if create.status < 200 or create.status >= 300:
            return PublishResult(False, self.platform, reason=f"Instagram media create failed: HTTP {create.status}")
        creation_id = str(create.data.get("id") or "")
        if not creation_id:
            return PublishResult(False, self.platform, reason="Instagram response missing media container id")

        published = self._fetch(
            "POST",
            self._url("media_publish"),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            body=form_body({"access_token": self._token, "creation_id": creation_id}),
        )
        if published.status < 200 or published.status >= 300:
            return PublishResult(False, self.platform, reason=f"Instagram publish failed: HTTP {published.status}")
        post_id = str(published.data.get("id") or "")
        if not post_id:
            return PublishResult(False, self.platform, reason="Instagram response missing published media id")
        return PublishResult(True, self.platform, post_id=post_id, reason="published",
                             data={"container_id": creation_id, "visibility": visibility})

    def _url(self, edge: str) -> str:
        return f"https://graph.facebook.com/{self._graph_version}/{self._business_id}/{edge}"


def _caption(post: dict) -> str:
    body = str(post.get("body") or post.get("caption") or "")
    hashtags = " ".join(f"#{str(h).lstrip('#')}" for h in (post.get("hashtags") or []) if str(h).strip())
    return " ".join(x for x in (body, hashtags) if x).strip()


def _looks_like_video(url: str) -> bool:
    return url.lower().split("?", 1)[0].endswith((".mp4", ".mov", ".m4v"))


def _truthy(value) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}
