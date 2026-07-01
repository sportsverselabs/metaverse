"""Storyboard builder tests — prompt -> 30s VideoProject of safe generated visuals. Offline."""

import re

from creative.models import SOURCE_GENERATED, SOURCE_OWNER_UPLOAD, VideoProject
from creative.storyboard import build_from_prompt, plan_scenes
from creative.store import VideoProjectStore
from sports.api_football_client import APIFootballClient
from sports.cache import SportsCache
from sports.context import SportsContext
from sports.espn_client import ESPNClient
from sports.health import SportsApiHealthMonitor
from sports.hub import SportsDataHub


def _offline_context(tmp_path):
    """SportsContext with an empty hub (no live data -> fallback ideas, no invented scores)."""
    empty = {"events": [], "articles": []}
    hub = SportsDataHub(
        cache=SportsCache(tmp_path / "c.db"),
        espn=ESPNClient(fetch=lambda url: empty),
        football=APIFootballClient(api_key="x", fetch=lambda p, par: {"errors": [], "response": []}),
        health=SportsApiHealthMonitor(state_path=tmp_path / "h.json"),
    )
    return SportsContext(hub=hub)


def _fake_renderer(path, text, seconds):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\x00")     # stand-in media file (no ffmpeg needed in tests)
    return path


def test_plan_scenes_sum_to_thirty_seconds(tmp_path):
    scenes = plan_scenes("make me 3 soccer video highlights", _offline_context(tmp_path), seconds=30)
    assert sum(s["seconds"] for s in scenes) == 30
    assert scenes[0]["role"] == "hook" and scenes[-1]["role"] == "cta"
    assert any(s["role"] == "beat" for s in scenes)


def test_build_from_prompt_creates_safe_generated_project(tmp_path):
    store = VideoProjectStore(tmp_path)
    p = build_from_prompt("make me 3 soccer video highlights", store=store,
                          context=_offline_context(tmp_path), scene_renderer=_fake_renderer)
    assert isinstance(p, VideoProject)
    # true 30s: clip out points sum to 30
    assert sum(c.out for c in p.clips) == 30
    # soccer-scoped + prompt-matched
    assert "soccer" in p.title.lower()
    # every clip is a SAFE generated visual with provenance
    assert all(c.source_kind == SOURCE_GENERATED and c.license_safe for c in p.clips)
    # media-license note present; nothing published
    assert "no real match footage" in p.description.lower()
    assert p.status != "published"


def test_storyboard_does_not_invent_scores(tmp_path):
    p = build_from_prompt("3 soccer highlight videos", store=VideoProjectStore(tmp_path),
                          context=_offline_context(tmp_path), scene_renderer=_fake_renderer)
    blob = " ".join([p.title, p.description]
                    + [c.captions[0].text for c in p.clips if c.captions]
                    + [c.meta.get("basis", "") for c in p.clips])
    assert not re.search(r"\d+\s*[-–]\s*\d+", blob)   # no fabricated "2-1" scores


def test_generated_project_persists_and_reloads(tmp_path):
    store = VideoProjectStore(tmp_path)
    p = build_from_prompt("make me 3 soccer video highlights", store=store,
                          context=_offline_context(tmp_path), scene_renderer=_fake_renderer)
    reloaded = store.load(p.id)
    assert len(reloaded.clips) == len(p.clips)
    assert reloaded.clips[0].meta.get("source_kind") == SOURCE_GENERATED


def test_owner_upload_marks_provenance():
    from creative.models import Clip
    c = Clip(src="x.mp4", meta={"source_kind": SOURCE_OWNER_UPLOAD, "license": "owner-provided"})
    assert c.license_safe is True and c.source_kind == SOURCE_OWNER_UPLOAD
    # a clip with unknown provenance is NOT considered safe
    assert Clip(src="y.mp4").license_safe is False
