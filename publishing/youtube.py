"""YouTube Data API publisher.

Uses OAuth refresh-token credentials from `.env` and starts uploads as private
by default. The HTTP transport is injectable so tests remain fully offline.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from publishing.base import PublishResult
from publishing.http import HttpResponse, default_fetch, form_body, json_body

TOKEN_URL = "https://oauth2.googleapis.com/token"
UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status"
VIDEO_URL = "https://www.youtube.com/watch?v={video_id}"
_VISIBILITY = {"private", "unlisted", "public"}


class YouTubePublisher:
    platform = "youtube"

    def __init__(self, config=None,
                 fetch: Optional[Callable[..., HttpResponse]] = None) -> None:
        self.config = config
        self._fetch = fetch or default_fetch
        self._client_id = config.secret("YOUTUBE_CLIENT_ID") if config else None
        self._client_secret = config.secret("YOUTUBE_CLIENT_SECRET") if config else None
        self._refresh_token = config.secret("YOUTUBE_REFRESH_TOKEN") if config else None

    @property
    def configured(self) -> bool:
        return bool(self._client_id and self._client_secret and self._refresh_token)

    def publish(self, post: dict, *, visibility: str = "private") -> PublishResult:
        if not self.configured:
            return PublishResult(False, self.platform, reason="YouTube not configured")

        video_path = _media_path(post)
        if not video_path:
            return PublishResult(False, self.platform, reason="YouTube upload requires video_path/media_path")
        path = Path(video_path)
        if not path.exists() or not path.is_file():
            return PublishResult(False, self.platform, reason="video file not found")

        token = self._access_token()
        if not token.ok:
            return token

        privacy = visibility if visibility in _VISIBILITY else "private"
        meta = {
            "snippet": {
                "title": str(post.get("title") or "Sportsverse upload")[:100],
                "description": _description(post),
                "tags": _tags(post),
                "categoryId": str(post.get("category_id") or "17"),
            },
            "status": {
                "privacyStatus": privacy,
                "selfDeclaredMadeForKids": bool(post.get("made_for_kids", False)),
            },
        }
        init = self._fetch(
            "POST",
            UPLOAD_URL,
            headers={
                "Authorization": f"Bearer {token.data['access_token']}",
                "Content-Type": "application/json; charset=UTF-8",
                "X-Upload-Content-Type": post.get("mime_type") or "video/mp4",
                "X-Upload-Content-Length": str(path.stat().st_size),
            },
            body=json_body(meta),
        )
        if init.status < 200 or init.status >= 300:
            return PublishResult(False, self.platform, reason=f"YouTube upload init failed: HTTP {init.status}")

        upload_url = init.headers.get("Location") or init.headers.get("location") or init.data.get("upload_url")
        if not upload_url:
            return PublishResult(False, self.platform, reason="YouTube upload URL missing")

        final = self._fetch(
            "PUT",
            upload_url,
            headers={"Authorization": f"Bearer {token.data['access_token']}",
                     "Content-Type": post.get("mime_type") or "video/mp4"},
            body=path.read_bytes(),
            timeout=120.0,
        )
        if final.status < 200 or final.status >= 300:
            return PublishResult(False, self.platform, reason=f"YouTube upload failed: HTTP {final.status}")

        video_id = str(final.data.get("id") or "")
        if not video_id:
            return PublishResult(False, self.platform, reason="YouTube response missing video id")
        return PublishResult(True, self.platform, post_id=video_id, url=VIDEO_URL.format(video_id=video_id),
                             reason="published", data={"visibility": privacy})

    def _access_token(self) -> PublishResult:
        resp = self._fetch(
            "POST",
            TOKEN_URL,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            body=form_body({
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "refresh_token": self._refresh_token,
                "grant_type": "refresh_token",
            }),
        )
        if resp.status < 200 or resp.status >= 300:
            return PublishResult(False, self.platform, reason=f"YouTube token refresh failed: HTTP {resp.status}")
        access_token = resp.data.get("access_token")
        if not access_token:
            return PublishResult(False, self.platform, reason="YouTube token response missing access token")
        return PublishResult(True, self.platform, data={"access_token": access_token})


def _media_path(post: dict) -> str:
    return str(post.get("video_path") or post.get("media_path") or post.get("file_path") or "").strip()


def _description(post: dict) -> str:
    body = str(post.get("body") or post.get("description") or "")
    hashtags = " ".join(f"#{str(h).lstrip('#')}" for h in (post.get("hashtags") or []) if str(h).strip())
    return "\n\n".join(x for x in (body, hashtags) if x).strip()


def _tags(post: dict) -> list[str]:
    return [str(h).lstrip("#") for h in (post.get("hashtags") or []) if str(h).strip()]
