"""TikTok Content Posting API uploader.

Uses TikTok's inbox upload endpoint for the ``video.upload`` scope. This sends
videos to the creator's TikTok inbox/drafts for manual completion rather than
posting directly to the public profile.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from publishing.base import PublishResult
from publishing.http import HttpResponse, default_fetch, form_body, json_body

TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
INIT_URL = "https://open.tiktokapis.com/v2/post/publish/inbox/video/init/"
_DRAFT_VISIBILITIES = {"private", "draft", "self_only", "inbox"}


class TikTokPublisher:
    platform = "tiktok"

    def __init__(self, config=None,
                 fetch: Optional[Callable[..., HttpResponse]] = None) -> None:
        self.config = config
        self._fetch = fetch or default_fetch
        self._access_token = config.secret("TIKTOK_ACCESS_TOKEN") if config else None
        self._client_key = config.secret("TIKTOK_CLIENT_KEY") if config else None
        self._client_secret = config.secret("TIKTOK_CLIENT_SECRET") if config else None
        self._refresh_token = config.secret("TIKTOK_REFRESH_TOKEN") if config else None

    @property
    def configured(self) -> bool:
        return bool(self._access_token or (self._client_key and self._client_secret and self._refresh_token))

    def publish(self, post: dict, *, visibility: str = "private") -> PublishResult:
        if not self.configured:
            return PublishResult(False, self.platform, reason="TikTok not configured")

        requested_visibility = str(visibility).strip().lower()
        if requested_visibility not in _DRAFT_VISIBILITIES:
            return PublishResult(False, self.platform,
                                 reason="TikTok direct public publishing is disabled; use draft/private")

        token = self._user_access_token()
        if not token.ok:
            return token

        media_url = str(post.get("media_url") or post.get("video_url") or "").strip()
        video_path = str(post.get("video_path") or post.get("media_path") or post.get("file_path") or "").strip()
        source_info: dict
        upload_path: Path | None = None
        if media_url:
            source_info = {"source": "PULL_FROM_URL", "video_url": media_url}
        elif video_path:
            upload_path = Path(video_path)
            if not upload_path.exists() or not upload_path.is_file():
                return PublishResult(False, self.platform, reason="video file not found")
            size = upload_path.stat().st_size
            source_info = {
                "source": "FILE_UPLOAD",
                "video_size": size,
                "chunk_size": size,
                "total_chunk_count": 1,
            }
        else:
            return PublishResult(False, self.platform, reason="TikTok publishing requires media_url or video_path")

        init = self._fetch(
            "POST",
            INIT_URL,
            headers={"Authorization": f"Bearer {token.data['access_token']}",
                     "Content-Type": "application/json; charset=UTF-8"},
            body=json_body({"source_info": source_info}),
        )
        if init.status < 200 or init.status >= 300:
            return PublishResult(False, self.platform, reason=f"TikTok publish init failed: HTTP {init.status}")
        err = init.data.get("error") or {}
        if err.get("code") and err.get("code") != "ok":
            return PublishResult(False, self.platform, reason=f"TikTok error: {err.get('code')}")
        data = init.data.get("data") or {}
        publish_id = str(data.get("publish_id") or "")
        if not publish_id:
            return PublishResult(False, self.platform, reason="TikTok response missing publish id")

        upload_url = data.get("upload_url")
        if upload_path is not None:
            if not upload_url:
                return PublishResult(False, self.platform, reason="TikTok upload URL missing")
            video_bytes = upload_path.read_bytes()
            uploaded = self._fetch(
                "PUT",
                upload_url,
                headers={
                    "Content-Type": post.get("mime_type") or "video/mp4",
                    "Content-Length": str(len(video_bytes)),
                    "Content-Range": f"bytes 0-{len(video_bytes) - 1}/{len(video_bytes)}",
                },
                body=video_bytes,
                timeout=120.0,
            )
            if uploaded.status < 200 or uploaded.status >= 300:
                return PublishResult(False, self.platform, reason=f"TikTok upload failed: HTTP {uploaded.status}")

        return PublishResult(True, self.platform, post_id=publish_id, reason="uploaded to TikTok inbox",
                             data={"mode": "inbox_upload",
                                   "source": source_info["source"],
                                   "requires_creator_completion": True})

    def _user_access_token(self) -> PublishResult:
        if self._access_token:
            return PublishResult(True, self.platform, data={"access_token": self._access_token})

        resp = self._fetch(
            "POST",
            TOKEN_URL,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            body=form_body({
                "client_key": self._client_key,
                "client_secret": self._client_secret,
                "grant_type": "refresh_token",
                "refresh_token": self._refresh_token,
            }),
        )
        if resp.status < 200 or resp.status >= 300:
            return PublishResult(False, self.platform, reason=f"TikTok token refresh failed: HTTP {resp.status}")
        access_token = resp.data.get("access_token")
        if not access_token:
            return PublishResult(False, self.platform, reason="TikTok token response missing access token")
        return PublishResult(True, self.platform, data={"access_token": access_token})
