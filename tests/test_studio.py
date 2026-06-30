"""Creative Studio dashboard (V1b) tests — offline; uses the real store under a temp root."""

import pytest

from dashboard import studio
from creative.store import VideoProjectStore


@pytest.fixture
def store(tmp_path, monkeypatch):
    s = VideoProjectStore(tmp_path / "video")
    monkeypatch.setattr(studio, "_store", lambda: s)
    return s


def test_overview_renders_heading(store):
    html = studio.overview_html()
    assert "<h2>Creative Studio</h2>" in html and "New demo project" in html


def test_demo_then_editor(store):
    res = studio.studio_action({"action": "demo"})
    pid = res["project"]
    assert "Demo project created" in res["message"]
    editor = studio.editor_html(pid)
    assert "Studio —" in editor and "Render draft" in editor and "Generate thumbnail" in editor


def test_caption_and_trim_and_reorder(store):
    pid = studio.studio_action({"action": "demo"})["project"]
    p = store.load(pid)
    cid = p.clips[0].id
    assert studio.studio_action({"action": "caption", "project": pid, "clip": cid, "text": "New text"})["message"]
    assert store.load(pid).clips[0].captions[0].text == "New text"
    studio.studio_action({"action": "trim", "project": pid, "clip": cid, "in_": "1.5", "out": "4"})
    reloaded = store.load(pid)
    assert reloaded.clips[0].in_ == 1.5 and reloaded.clips[0].out == 4.0
    # edit history grew (created + caption + trim)
    assert len(reloaded.edit_history) >= 3


def test_render_reports_clearly_without_media(store):
    # Demo clips point at nonexistent media; render should fail cleanly (no crash, no fake success).
    pid = studio.studio_action({"action": "demo"})["project"]
    res = studio.studio_action({"action": "render", "project": pid})
    assert "error" in res  # ffmpeg missing OR media missing — either way a clear error, never ok


def test_unknown_and_bad_project(store):
    assert "error" in studio.studio_action({"action": "nope", "project": "x"})
    assert "error" in studio.studio_action({"action": "trim", "project": "../etc"})


def test_media_path_rejects_traversal(store):
    pid = studio.studio_action({"action": "demo"})["project"]
    assert studio.media_path(pid, "../../etc/passwd") is None
    assert studio.media_path("bad id!", "x.mp4") is None
    assert studio.media_path(pid, "render_draft.mp4") is None  # not rendered yet → missing file
