"""Phase 5 publishing tests: offline transports, owner gate, and review updates."""

import json

from publishing.base import PublishResult
from publishing.http import HttpResponse
from publishing.instagram import InstagramPublisher
from publishing.service import PublishingService
from publishing.tiktok import TikTokPublisher
from publishing.youtube import YouTubePublisher
from review.models import STATUS_OWNER_APPROVED, STATUS_PUBLISHED, make_review_item
from review.store import ReviewStore


class FakeConfig:
    def __init__(self, secrets=None, settings=None):
        self._secrets = secrets or {}
        self._settings = settings or {}

    def secret(self, key):
        return self._secrets.get(key)

    def get(self, key, default=None):
        return self._settings.get(key, default)


def test_youtube_not_configured_refuses():
    pub = YouTubePublisher(config=FakeConfig())
    assert pub.configured is False
    result = pub.publish({"platform": "youtube", "video_path": "missing.mp4"})
    assert result.ok is False
    assert "not configured" in result.reason.lower()


def test_youtube_upload_uses_private_visibility_and_transport(tmp_path):
    video = tmp_path / "clip.mp4"
    video.write_bytes(b"fake video")
    calls = []

    def fetch(method, url, *, headers=None, body=None, timeout=30.0):
        calls.append({"method": method, "url": url, "headers": headers or {}, "body": body})
        if "oauth2.googleapis.com" in url:
            return HttpResponse(200, {"access_token": "access"})
        if method == "POST":
            return HttpResponse(200, {}, {"Location": "https://upload.youtube.test/session"})
        return HttpResponse(200, {"id": "yt123"})

    cfg = FakeConfig({"YOUTUBE_CLIENT_ID": "cid", "YOUTUBE_CLIENT_SECRET": "sec", "YOUTUBE_REFRESH_TOKEN": "rtok"})
    result = YouTubePublisher(config=cfg, fetch=fetch).publish(
        {"platform": "youtube", "title": "Clip", "body": "hello", "hashtags": ["nba"], "video_path": str(video)}
    )
    assert result.ok is True
    assert result.post_id == "yt123"
    metadata = json.loads(calls[1]["body"].decode("utf-8"))
    assert metadata["status"]["privacyStatus"] == "private"
    assert calls[-1]["method"] == "PUT"


def test_tiktok_upload_uses_inbox_endpoint_with_public_media_url():
    calls = []

    def fetch(method, url, *, headers=None, body=None, timeout=30.0):
        calls.append({"method": method, "url": url, "headers": headers or {}, "body": body})
        return HttpResponse(200, {"data": {"publish_id": "tk123"}, "error": {"code": "ok"}})

    pub = TikTokPublisher(config=FakeConfig({"TIKTOK_ACCESS_TOKEN": "tok"}), fetch=fetch)
    result = pub.publish({"platform": "tiktok", "body": "caption", "media_url": "https://example.com/clip.mp4"})
    assert result.ok is True
    assert result.post_id == "tk123"
    assert result.reason == "uploaded to TikTok inbox"
    assert result.data["requires_creator_completion"] is True
    assert calls[0]["url"].endswith("/v2/post/publish/inbox/video/init/")
    body = json.loads(calls[0]["body"].decode("utf-8"))
    assert "post_info" not in body
    assert body["source_info"]["source"] == "PULL_FROM_URL"


def test_tiktok_public_visibility_is_not_direct_posted():
    calls = []

    def fetch(method, url, *, headers=None, body=None, timeout=30.0):
        calls.append({"method": method, "url": url})
        return HttpResponse(200, {"data": {"publish_id": "tk123"}, "error": {"code": "ok"}})

    pub = TikTokPublisher(config=FakeConfig({"TIKTOK_ACCESS_TOKEN": "tok"}), fetch=fetch)
    result = pub.publish(
        {"platform": "tiktok", "media_url": "https://example.com/clip.mp4"},
        visibility="public",
    )
    assert result.ok is False
    assert "direct public publishing is disabled" in result.reason
    assert calls == []


def test_tiktok_file_upload_sends_required_transfer_headers(tmp_path):
    video = tmp_path / "clip.mp4"
    video.write_bytes(b"fake video")
    calls = []

    def fetch(method, url, *, headers=None, body=None, timeout=30.0):
        calls.append({"method": method, "url": url, "headers": headers or {}, "body": body, "timeout": timeout})
        if method == "POST":
            return HttpResponse(
                200,
                {"data": {"publish_id": "tk456", "upload_url": "https://upload.tiktok.test/video"}, "error": {"code": "ok"}},
            )
        return HttpResponse(200, {})

    pub = TikTokPublisher(config=FakeConfig({"TIKTOK_ACCESS_TOKEN": "tok"}), fetch=fetch)
    result = pub.publish({"platform": "tiktok", "video_path": str(video)})
    assert result.ok is True
    assert calls[1]["method"] == "PUT"
    assert calls[1]["headers"]["Content-Length"] == str(len(b"fake video"))
    assert calls[1]["headers"]["Content-Range"] == "bytes 0-9/10"
    assert calls[1]["body"] == b"fake video"


def test_instagram_public_publish_requires_explicit_enable():
    pub = InstagramPublisher(config=FakeConfig({"IG_ACCESS_TOKEN": "tok", "IG_BUSINESS_ID": "ig1"}))
    result = pub.publish({"platform": "instagram", "image_url": "https://example.com/post.jpg"}, visibility="public")
    assert result.ok is False
    assert "disabled" in result.reason.lower()


def test_service_refuses_unapproved_posts(tmp_path):
    service = PublishingService(config=FakeConfig(), publishers={}, posts_log=tmp_path / "publish.jsonl", alert=None)
    result = service.publish({"platform": "youtube"}, platform="youtube", approved=False)
    assert result.ok is False
    assert "approval" in result.reason.lower()


def test_service_publishes_owner_approved_review_item(tmp_path):
    class FakePublisher:
        platform = "youtube"
        configured = True

        def publish(self, post, *, visibility="private"):
            assert post["review_id"]
            assert visibility == "private"
            return PublishResult(True, "youtube", post_id="yt999", url="https://youtu.be/yt999", reason="published")

    store = ReviewStore(base_dir=tmp_path / "review")
    item = make_review_item("video_idea_draft", "approved body", 0, {"risk_score": 0, "passed": True})
    item.status = STATUS_OWNER_APPROVED
    store.add(item)
    alerts = []
    service = PublishingService(
        config=FakeConfig(),
        review_store=store,
        publishers={"youtube": FakePublisher()},
        posts_log=tmp_path / "publish.jsonl",
        alert=alerts.append,
    )
    result = service.publish_review_item(item.id, platform="youtube", visibility="private")
    saved = store.get(item.id)
    assert result.ok is True
    assert saved.status == STATUS_PUBLISHED
    assert saved.published is True
    assert saved.post_id == "yt999"
    assert alerts and "Published" in alerts[0]


def test_service_history_reads_recent_publish_log(tmp_path):
    log = tmp_path / "publish.jsonl"
    log.write_text(
        "\n".join([
            json.dumps({"ts": "2026-01-02T00:00:00", "review_id": "rv1", "platform": "youtube",
                        "ok": True, "post_id": "yt1", "url": "https://youtu.be/yt1",
                        "reason": "published", "visibility": "private", "dry_run": False}),
            json.dumps({"ts": "2026-01-01T00:00:00", "review_id": "old", "platform": "youtube",
                        "ok": False, "reason": "failed", "visibility": "private"}),
        ]),
        encoding="utf-8",
    )
    service = PublishingService(config=FakeConfig(), publishers={}, posts_log=log, alert=None)
    rows = service.history(limit=1)
    assert rows == [{
        "ts": "2026-01-02T00:00:00",
        "review_id": "rv1",
        "platform": "youtube",
        "ok": True,
        "status": "published",
        "post_id": "yt1",
        "url": "https://youtu.be/yt1",
        "reason": "published",
        "visibility": "private",
        "dry_run": False,
    }]


def test_tiktok_refreshes_access_token_when_only_refresh_credentials_exist():
    calls = []

    def fetch(method, url, *, headers=None, body=None, timeout=30.0):
        calls.append({"method": method, "url": url, "headers": headers or {}, "body": body})
        if url.endswith("/v2/oauth/token/"):
            return HttpResponse(200, {"access_token": "fresh-access"})
        return HttpResponse(200, {"data": {"publish_id": "tk789"}, "error": {"code": "ok"}})

    pub = TikTokPublisher(
        config=FakeConfig({
            "TIKTOK_CLIENT_KEY": "ckey",
            "TIKTOK_CLIENT_SECRET": "csecret",
            "TIKTOK_REFRESH_TOKEN": "refresh",
        }),
        fetch=fetch,
    )
    result = pub.publish({"platform": "tiktok", "media_url": "https://example.com/clip.mp4"})
    assert result.ok is True
    assert calls[0]["url"].endswith("/v2/oauth/token/")
    assert b"grant_type=refresh_token" in calls[0]["body"]
    assert calls[1]["headers"]["Authorization"] == "Bearer fresh-access"
